import os, csv, sys, time
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")                # ex: "Marcos-Lopes80"
PROJECT_NUMBER = int(os.getenv("PROJECT_NUMBER", "3"))
VIEW_NAME = os.getenv("VIEW_NAME", "").strip() or None

API = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def gql(query, variables=None):
    r = requests.post(API, headers=HEADERS, json={"query": query, "variables": variables or {}}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

def get_user_id(login):
    q = """
    query($login:String!){
      user(login:$login){ id login }
    }
    """
    d = gql(q, {"login": login})
    if not d or not d.get("user"):
        raise RuntimeError(f"User not found: {login}")
    return d["user"]["id"]

def get_project(user_login, project_number):
    q = """
    query($login:String!, $number:Int!){
      user(login:$login){
        projectV2(number:$number){
          id title url number
          fields(first:100){
            nodes{
              ... on ProjectV2FieldCommon { id name dataType }
              ... on ProjectV2SingleSelectField { id name dataType options { id name } }
            }
          }
          views(first:20){ nodes { id name filter } }
        }
      }
    }
    """
    d = gql(q, {"login": user_login, "number": project_number})
    p = d["user"]["projectV2"]
    if not p:
        raise RuntimeError(f"Project not found: {user_login} / #{project_number}")
    return p

def list_items(project_id, per_page=100):
    q = """
    query($pid:ID!, $after:String){
      node(id:$pid){
        ... on ProjectV2{
          items(first:100, after:$after){
            pageInfo{ hasNextPage endCursor }
            nodes{
              id
              content{
                __typename
                ... on Issue {
                  id number title url state
                  repository{ nameWithOwner }
                  assignees(first:10){ nodes{ login } }
                  labels(first:20){ nodes{ name } }
                  milestone{ title dueOn }
                  createdAt updatedAt
                }
                ... on PullRequest {
                  id number title url state
                  repository{ nameWithOwner }
                  assignees(first:10){ nodes{ login } }
                  labels(first:20){ nodes{ name } }
                  milestone{ title dueOn }
                  createdAt updatedAt
                }
                ... on DraftIssue {
                  title
                }
              }
              fieldValues(first:50){
                nodes{
                  __typename
                  ... on ProjectV2ItemFieldTextValue { field { ... on ProjectV2FieldCommon { id name } } text }
                  ... on ProjectV2ItemFieldNumberValue { field { ... } number }
                  ... on ProjectV2ItemFieldDateValue { field { ... } date }
                  ... on ProjectV2ItemFieldSingleSelectValue { field { ... } name optionId }
                  ... on ProjectV2ItemFieldIterationValue { field { ... } title startDate duration }
                  ... on ProjectV2ItemFieldMilestoneValue { field { ... } milestone { title dueOn } }
                  ... on ProjectV2ItemFieldRepositoryValue { field { ... } repository { nameWithOwner } }
                  ... on ProjectV2ItemFieldPullRequestValue { field { ... } pullRequests(first:10){ nodes{ number url } } }
                  ... on ProjectV2ItemFieldUserValue { field { ... } users(first:10){ nodes{ login } } }
                }
              }
            }
          }
        }
      }
    }
    """
    items = []
    after = None
    while True:
        d = gql(q, {"pid": project_id, "after": after})
        node = d["node"]["items"]
        items.extend(node["nodes"])
        if node["pageInfo"]["hasNextPage"]:
            after = node["pageInfo"]["endCursor"]
            time.sleep(0.3)
        else:
            break
    return items

def flatten_item(item, field_map):
    # base columns
    row = {
        "project_item_id": item["id"],
        "type": None,
        "title": None,
        "url": None,
        "repo": None,
        "number": None,
        "state": None,
        "assignees": None,
        "labels": None,
        "milestone": None,
        "milestone_due": None,
        "createdAt": None,
        "updatedAt": None,
    }

    content = item.get("content") or {}
    t = content.get("__typename")
    row["type"] = t

    if t in ("Issue", "PullRequest"):
        row["title"] = content.get("title")
        row["url"] = content.get("url")
        row["number"] = content.get("number")
        row["state"] = content.get("state")
        repo = content.get("repository") or {}
        row["repo"] = repo.get("nameWithOwner")
        assignees = content.get("assignees", {}).get("nodes", [])
        row["assignees"] = ", ".join([a["login"] for a in assignees]) if assignees else ""
        labels = content.get("labels", {}).get("nodes", [])
        row["labels"] = ", ".join([l["name"] for l in labels]) if labels else ""
        ms = content.get("milestone")
        if ms:
            row["milestone"] = ms.get("title")
            row["milestone_due"] = ms.get("dueOn")
        row["createdAt"] = content.get("createdAt")
        row["updatedAt"] = content.get("updatedAt")
    elif t == "DraftIssue":
        row["title"] = content.get("title")
        row["url"] = ""
    else:
        # outros tipos raros
        pass

    # project custom fields
    for fv in (item.get("fieldValues", {}) or {}).get("nodes", []):
        f = fv.get("field") or {}
        fname = f.get("name")
        if not fname:
            continue
        key = f"field:{fname}"
        # map valores
        typ = fv.get("__typename")
        if typ == "ProjectV2ItemFieldTextValue":
            row[key] = fv.get("text")
        elif typ == "ProjectV2ItemFieldNumberValue":
            row[key] = fv.get("number")
        elif typ == "ProjectV2ItemFieldDateValue":
            row[key] = fv.get("date")
        elif typ == "ProjectV2ItemFieldSingleSelectValue":
            row[key] = fv.get("name")
        elif typ == "ProjectV2ItemFieldIterationValue":
            row[key] = fv.get("title")
        elif typ == "ProjectV2ItemFieldMilestoneValue":
            ms = fv.get("milestone") or {}
            row[key] = ms.get("title")
        elif typ == "ProjectV2ItemFieldRepositoryValue":
            repo = fv.get("repository") or {}
            row[key] = repo.get("nameWithOwner")
        elif typ == "ProjectV2ItemFieldPullRequestValue":
            prs = fv.get("pullRequests", {}).get("nodes", [])
            row[key] = ", ".join([f"#{p['number']}" for p in prs]) if prs else ""
        elif typ == "ProjectV2ItemFieldUserValue":
            us = fv.get("users", {}).get("nodes", [])
            row[key] = ", ".join([u["login"] for u in us]) if us else ""
        else:
            # fallback
            row[key] = ""
    return row

def simple_view_filter(df: pd.DataFrame, view_filter: str) -> pd.DataFrame:
    """
    Aplicador simples de filtro da view: suporta alguns termos básicos
    ex.: "assignee:@me status:Doing label:prio:alta"
    Aqui vamos suportar chaves 'status', 'assignee', 'label' aproximando dos campos:
      - status -> tenta coluna 'field:Status'
      - assignee -> 'assignees' contém o login
      - label/labels -> coluna 'labels'
    (Se a sua view tiver filtros avançados, exportaremos sem filtro)
    """
    if not view_filter:
        return df
    s = view_filter.lower()

    # status:
    import re
    m = re.findall(r"status:([^ \n]+)", s)
    if m and "field:Status" in df.columns:
        df = df[df["field:Status"].str.lower().fillna("").isin([x.lower() for x in m])]

    # assignee:
    m = re.findall(r"(?:assignee|assignees):([^ \n]+)", s)
    if m:
        want = [x.replace("@", "").lower() for x in m]
        df = df[df["assignees"].fillna("").str.lower().apply(
            lambda txt: any(w in txt for w in want)
        )]

    # label:
    m = re.findall(r"(?:label|labels):([^ \n]+)", s)
    if m:
        want = [x.lower() for x in m]
        df = df[df["labels"].fillna("").str.lower().apply(
            lambda txt: any(w in txt for w in want)
        )]
    return df

def main():
    if not GITHUB_TOKEN:
        print("ERRO: GITHUB_TOKEN vazio no .env")
        sys.exit(1)
    pid = get_project(GITHUB_USER, PROJECT_NUMBER)
    project_id = pid["id"]
    title = pid["title"]
    views = pid.get("views", {}).get("nodes", [])
    view_filter = None
    if VIEW_NAME:
        for v in views:
            if v["name"].strip().lower() == VIEW_NAME.strip().lower():
                view_filter = v.get("filter") or ""
                break

    print(f"[INFO] Projeto: {title} (#{PROJECT_NUMBER})")
    print(f"[INFO] View selecionada: {VIEW_NAME or '(todas)'}")
    if view_filter:
        print(f"[INFO] Filtro da view: {view_filter}")

    items = list_items(project_id)
    # coletar mapa de campos (opcional)
    field_map = {}  # não precisamos agora, mas deixo para extensões futuras
    rows = [flatten_item(it, field_map) for it in items]
    if not rows:
        print("[INFO] Nenhum item encontrado.")
        return

    df = pd.DataFrame(rows)
    if view_filter:
        df = simple_view_filter(df, view_filter)

    out_csv = f"project_{PROJECT_NUMBER}_export.csv"
    df.to_csv(out_csv, index=False, quoting=csv.QUOTE_ALL)
    print(f"[OK] Exportado: {out_csv}  ({len(df)} linhas)")

if __name__ == "__main__":
    main()
