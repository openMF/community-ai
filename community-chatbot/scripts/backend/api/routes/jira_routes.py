from fastapi import APIRouter, HTTPException
from backend.models.schemas import JiraQueryRequest, JiraQueryResponse
from backend.services.jira_service import get_jira_service

router = APIRouter(tags=["jira"])

@router.options("/query")
async def options_jira_query():
    return {}

@router.post("/query", response_model=JiraQueryResponse)
async def query_jira(request: JiraQueryRequest):
    try:
        service = get_jira_service()
        if request.use_fallback:
            result = service.intelligent_agent_run(request.query)
        else:
            try:
                response = service.run_agent(request.query)
                result = {
                    "response": response,
                    "method_used": "agent",
                    "query_used": request.query,
                    "success": True
                }
            except Exception as e:
                result = {
                    "response": f"Agent failed: {str(e)}",
                    "method_used": "agent",
                    "query_used": request.query,
                    "success": False
                }
        return JiraQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/direct-jql")
async def direct_jql_query(jql_query: str):
    try:
        service = get_jira_service()
        result = service.direct_jql_query(jql_query)
        return {"jql_query": jql_query, "result": result, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate-jql")
async def generate_jql(natural_query: str):
    try:
        service = get_jira_service()
        generated_jql = service.generate_jql(natural_query)
        return {"natural_query": natural_query, "generated_jql": generated_jql, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
