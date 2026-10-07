from typing import Any
from pathlib import Path

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    single_row
)
from connectors import dynamo


class CustomAPIOperation(EndpointHandlerTemplate):

    connector = dynamo
    query_path = Path(__file__).with_name("query.sql")

    
    def bind_parameters(self) -> list:
    
        body = self.body

        # aux_ref_id = body.get("auxiliaryReferenceId")
        # identifier = body.get("identifier")
        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

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
                "lastAvaliableBalanceAmount": row.get("lastAvailableBalanceAmount", ""),
                "lastAvaliableBalanceCurrency": row.get("lastAvailableBalanceCurrency", ""),
                "creditLimit": row.get("creditLimit", ""),
        }



OPERATION_CLASS = CustomAPIOperation
