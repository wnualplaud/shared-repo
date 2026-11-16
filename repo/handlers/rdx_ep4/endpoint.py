from typing import Any
from pathlib import Path

from datetime import datetime

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    single_row,
    require_rows,
    require_subtype,
    require_language,
    select_by_language,
    TZ_TH, athena_to_th_iso,
    MART_SUBTYPES,
    to_amount,
    fill_null,
)
from connectors import athena, dynamo
import sql_builder



ACCOUNT_CHECK_PATH = Path(__file__).with_name("account_check.sql")



class CustomAPIOperation(EndpointHandlerTemplate):

    connector = athena
    query_path = Path(__file__).with_name("query.sql")
    REQUIRED_FIELDS = (
            "auxiliaryReferenceId",
            "accountId",
            "accountSubType",
            "fromBookingDateTime",
            "toBookingDateTime",
        )

    def handle(self):

        self.validate()
        require_language(self.body.get("language"))
        require_subtype(self.body.get("accountSubType"))
        self.account = self.check_account()
        return super().handle()
    
    
    def check_account(self):
        
        body = self.body
        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

        query, values = sql_builder.bind(
            sql_builder.load_query(ACCOUNT_CHECK_PATH),
            params={
                        "account_id": account_id,
                        "mart_account_sub_type": MART_SUBTYPES[account_sub_type],
                    }

        )

        rows = dynamo.execute(query, values)

        return single_row(rows)

    
    def bind_parameters(self) -> dict:

        body = self.body

        account_id = self.account["accountId"]
        src_stm_id = self.account["src_stm_id"]

        from_booking_dttm = body.get("fromBookingDateTime")
        to_booking_dttm = body.get("toBookingDateTime")

        from_dttm = (
            datetime.fromisoformat(from_booking_dttm) 
        ).astimezone(TZ_TH)

        to_dttm = (
            datetime.fromisoformat(to_booking_dttm) 
        ).astimezone(TZ_TH)

        # the :names in query.sql; data_dt (varchar partition) is the Thai date (assumed, r06 c03)
        return {
            "from_data_dt": from_dttm.date().isoformat(), 
            "to_data_dt": to_dttm.date().isoformat(),  
            "src_stm_id": src_stm_id,
            "from_booking_dttm": from_dttm.isoformat(), 
            "to_booking_dttm": to_dttm.isoformat(),               
            "account_id": account_id
        }


    def build_mapping(self, query_result: Any):

        aux_ref_id = self.body.get("auxiliaryReferenceId")
        account_id = self.body.get("accountId")
        language = self.body.get("language")

        transaction_entries = [
            {
                "bookingDateTime": fill_null(athena_to_th_iso(row.get("bookingDateTime")), kind="timestamp"),                                       # 1.3.1
                "valueDateTime": fill_null(athena_to_th_iso(row.get("valueDateTime")), kind="timestamp"),                                           # 1.3.2
                "subAccountLevelMaturityDate": fill_null(athena_to_th_iso(row.get("subAccountLevelMaturityDate")), kind="timestamp"),               # 1.3.3
                "domainCode": fill_null(row.get("domainCode")),                                             # 1.3.4.1
                "familyCode": fill_null(row.get("familyCode")),                                             # 1.3.4.2
                "subFamilyCode": fill_null(row.get("subFamilyCode")),                                       # 1.3.4.3
                "proprietaryBankTransactionCode": fill_null(row.get("proprietaryBankTransactionCode")),         # 1.3.5
                "proprietaryBankTransactionDescription": fill_null(row.get("proprietaryBankTransactionDescription")),  # 1.3.6
                "creditDebitIndicator": fill_null(row.get("creditDebitIndicator")),                             # 1.3.7
                "amount": to_amount(row.get("amount")),                                                         # 1.3.8
                "amountCurrency": fill_null(row.get("amountCurrency")),                                         # 1.3.9
                "transactionId": fill_null(row.get("transactionId")),                                           # 1.3.10
                "transactionRef": fill_null(row.get("transactionRef")),                                         # 1.3.11
                "transactionInformation": fill_null(row.get("transactionInformation")),                         # 1.3.12
                "creditorAccountId": fill_null(row.get("creditorAccountId")),                                   # 1.3.13
                "creditorAccountName": fill_null(row.get("creditorAccountName")),                               # 1.3.14
                "receivingInstitutionCode": fill_null(row.get("receivingInstitutionCode")),                     # 1.3.15
                "receivingInstitutionName": fill_null(row.get("receivingInstitutionName")),                     # 1.3.16
                "debtorAccountId": fill_null(row.get("debtorAccountId")),                                       # 1.3.17
                "debtorAccountName": fill_null(row.get("debtorAccountName")),                                   # 1.3.18
                "sendingInstitutionCode": fill_null(row.get("sendingInstitutionCode")),                         # 1.3.19
                "sendingInstitutionName": fill_null(row.get("sendingInstitutionName")),                         # 1.3.20
                "merchantName": fill_null(select_by_language(                                                  # 1.3.21
                    language=language,
                    th_value=row.get("merchantName"),
                    en_value=row.get("merchantNameEn"),
                )),
            }

            for row in query_result
        ]

        require_rows(transaction_entries, detail="No transactions found")

        return {
            "auxiliaryReferenceId": aux_ref_id,                                                  # 1.1
            "accountId": account_id,                                                             # 1.2
            "transactionEntries": transaction_entries,                                           # 1.3
        }



OPERATION_CLASS = CustomAPIOperation
