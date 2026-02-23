from pathlib import Path
from src.types.pg_ai_types import SkillContent, DatabaseResult, MCPTools
from src.connectors.pg_connector import PGConnector
from sqlalchemy import text
# import pandas as pd
import polars as pl

conn = PGConnector(db_user="", db_port="", db_pass="", db_name="", db_host = "")

async def read_business_logic():
    try:
        with open(Path("pg_skills")/"business-logic"/"SKILL.md", encoding="utf-8") as bl:
            content = bl.read()
        return SkillContent(content=content)
    except Exception as e:
        raise e

async def load_skill(skill_name: str):
    """
    Load the respective skill to get the references for table schema, query instructions, etc.,
    """
    try:
        with open(Path("pg_skills")/skill_name/"SKILL.md", encoding="utf-8") as skill:
            content = skill.read()
        return SkillContent(content=content)
    except Exception as e:
        raise e
    
async def execute_query(sql_query: str):
    """
    Tool to execute the prepared sql query in the Postgres database
    """
    db = await conn.connect()
    try:
        result = await db.fetch_all(text(sql_query))
        dataframe = pl.DataFrame(result)
        return DatabaseResult(sql_query=sql_query,sql_result=dataframe)
    except Exception as e:
        raise e
    finally:
        await db.disconnect() 


def get_mcp_tools():
    return MCPTools(
        mcp_tools=[read_business_logic, load_skill, execute_query]
    )