from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    require_subtype,
    single_row
)
from connectors import dynamo


class CustomAPIOperation(EndpointHandlerTemplate):

    connector = dynamo
    query_path = Path(__file__).with_name("query.sql")

    
    def bind_parameters(self) -> list:

        body = self.body

        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

        require_subtype(account_sub_type)

        return [account_id, account_sub_type]


    def build_mapping(self, rows: Any):
            
        body = self.body
        row = single_row(rows)
        auxiliary_ref_id = self.body.get("auxiliaryReferenceId")

        return {
                "auxiliaryReferenceId": auxiliary_ref_id,
                "accountId": row.get("accountId", ""),
                "lastLedgerBalanceAmount": row.get("lastLedgerBalanceAmount", ""),
                "lastLedgerBalanceCurrency": row.get("lastLedgerBalanceCurrency", ""),
                "lastAvailableBalanceAmount": row.get("lastAvailableBalanceAmount", ""),
                "lastAvailableBalanceCurrency": row.get("lastAvailableBalanceCurrency", ""),
                "creditLimit": row.get("creditLimit", ""),
        }



OPERATION_CLASS = CustomAPIOperation
