"""SQLAlchemy 模型注册入口：导入全部实体以完成 metadata 注册。

表结构与 docs/架构设计方案.md 第 7 章一一对应（rules/01）。
"""

from app.models.base import Base
from app.models.agent_session import AgentSession
from app.models.agent_step import AgentStep
from app.models.ai_query import AiQuery
from app.models.business_line import BusinessLine
from app.models.collect_log import CollectLog
from app.models.collect_task import CollectTask
from app.models.column_meta import ColumnMeta
from app.models.database_meta import DatabaseMeta
from app.models.datasource import Datasource
from app.models.hive_partition import HivePartition
from app.models.saved_query import SavedQuery
from app.models.sys_user import SysUser
from app.models.table_business_line import TableBusinessLine
from app.models.table_lineage import TableLineage
from app.models.table_meta import TableMeta
from app.models.table_subscription import TableSubscription
from app.models.table_usage import TableUsage
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.models.task_parameter import TaskParameter
from app.models.task_version import TaskVersion
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution

__all__ = ["Base"]
