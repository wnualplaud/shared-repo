from typing import Any
from pathlib import Path
import uuid
from datetime import datetime

from endpoint_handler_template import EndpointHandlerTemplate
from endpoint_handler_template import (
    single_row,
    require_rows,
    require_subtype,
    require_language,
    select_by_language,
    TZ_TH, athena_to_th_iso, iso_to_th_iso,
    MART_SUBTYPES,
    to_amount,
    to_api_subtype,
    fill_null,

)
from connectors import athena, dynamo
import sql_builder



ACCOUNT_DETAIL_PATH = Path(__file__).with_name("account_detail.sql")



class CustomAPIOperation(EndpointHandlerTemplate):

    connector = athena
    query_path = Path(__file__).with_name("statement.sql")
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
        self.account_detail = self.check_account()
        return super().handle()
    
    
    def check_account(self):
        
        body = self.body
        account_id = body.get("accountId")
        account_sub_type = body.get("accountSubType")

        query, values = sql_builder.bind(
            sql_builder.load_query(ACCOUNT_DETAIL_PATH),
            params={
                        "account_id": account_id,
                        "mart_account_sub_type": MART_SUBTYPES[account_sub_type],
                    }

        )

        rows = dynamo.execute(query, values)

        return single_row(rows)

    
    def bind_parameters(self) -> dict:

        body = self.body

        account_id = self.account_detail["accountId"]
        src_stm_id = self.account_detail["src_stm_id"]

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

        last_row = query_result[0] if query_result else None

        # group empty -> DynamoDB (assumed: openingDate)
        from_mart = last_row is not None and last_row.get("openingDate") not in (None, "")

        account_detail = self.account_detail
        header = last_row if from_mart else account_detail
        account_level_maturity = header.get("accountLevelMaturityDate") if from_mart else None

        body = self.body
        aux_ref_id = body.get("auxiliaryReferenceId")      
        language = body.get("language")

        statement_entries = [
            {
                "bookingDateTime": fill_null(athena_to_th_iso(row.get("bookingDateTime")), kind="timestamp"),                                       # 1.24.1
                "valueDateTime": fill_null(athena_to_th_iso(row.get("valueDateTime")), kind="timestamp"),                                           # 1.24.2
                "subAccountLevelMaturityDate": fill_null(athena_to_th_iso(row.get("subAccountLevelMaturityDate")), kind="timestamp"),               # 1.24.3
                "domainCode": fill_null(row.get("domainCode")),                                             # 1.24.4.1
                "familyCode": fill_null(row.get("familyCode")),                                             # 1.24.4.2
                "subFamilyCode": fill_null(row.get("subFamilyCode")),                                       # 1.24.4.3
                "proprietaryBankTransactionCode": fill_null(row.get("proprietaryBankTransactionCode")),         # 1.24.5
                "proprietaryBankTransactionDescription": fill_null(row.get("proprietaryBankTransactionDescription")),  # 1.24.6
                "creditDebitIndicator": fill_null(row.get("creditDebitIndicator")),                             # 1.24.7
                "amount": to_amount(row.get("amount")),                                                         # 1.24.8
                "amountCurrency": fill_null(row.get("amountCurrency")),                                         # 1.24.9

                # statement
                "balance": to_amount(row.get("balance")),                                            # 1.24.10
                "balanceCurrency": fill_null(row.get("balanceCurrency")),                                       # 1.24.11
                "processingBranchCode": fill_null(row.get("processingBranchCode")),                             # 1.24.12
                "processingBranchDescription": fill_null(row.get("processingBranchDescription")),               # 1.24.13
                "originCode": fill_null(row.get("originCode")),                                                 # 1.24.14
                "originDescription": fill_null(row.get("originDescription")),                                   # 1.24.15

                "transactionId": fill_null(row.get("transactionId")),                                           # 1.24.16
                "transactionRef": fill_null(row.get("transactionRef")),                                         # 1.24.17
                "transactionInformation": fill_null(row.get("transactionInformation")),                         # 1.24.18
                "creditorAccountId": fill_null(row.get("creditorAccountId")),                                   # 1.24.19
                "creditorAccountName": fill_null(row.get("creditorAccountName")),                               # 1.24.20
                "receivingInstitutionCode": fill_null(row.get("receivingInstitutionCode")),                     # 1.24.21
                "receivingInstitutionName": fill_null(row.get("receivingInstitutionName")),                     # 1.24.22
                "debtorAccountId": fill_null(row.get("debtorAccountId")),                                       # 1.24.23
                "debtorAccountName": fill_null(row.get("debtorAccountName")),                                   # 1.24.24
                "sendingInstitutionCode": fill_null(row.get("sendingInstitutionCode")),                         # 1.24.25
                "sendingInstitutionName": fill_null(row.get("sendingInstitutionName")),                         # 1.24.26
                "merchantName": fill_null(select_by_language(                                                  # 1.24.27
                    language=language,
                    th_value=row.get("merchantName"),
                    en_value=row.get("merchantNameEn"),
                )),
            }

            for row in query_result
        ]

        require_rows(statement_entries, detail="No transactions found")

        return {
            "creationDateTime": fill_null(datetime.now(TZ_TH).isoformat(timespec="seconds"), kind="timestamp"),       # 1.1
            "statementId": str(uuid.uuid4()),                                            # 1.2
            "auxiliaryReferenceId": aux_ref_id,                                          # 1.3
            "institutionName": fill_null(account_detail.get("institutionName")),                   # 1.4
            "accountId": fill_null(account_detail.get("accountId")),                               # 1.5

            # account/
            "ownerType": fill_null(header.get("ownerType")),                               # 1.6
            "productAccountType": fill_null(header.get("accountType")),                           # 1.7
            "accountSubType": fill_null(to_api_subtype(header.get("accountSubType"))),                     # 1.8
            "accountStatus": fill_null(header.get("accountStatus")),                       # 1.9
            "accountName": fill_null(select_by_language(
                language=language,
                th_value=account_detail.get("accountName"),
                en_value=account_detail.get("accountNameEn"),
            )),                           # 1.10
            "accountOwner": fill_null(header.get("accountOwner")),                         # 1.11
            "openingDate": fill_null(
                athena_to_th_iso(header.get("openingDate")) if from_mart             
                else iso_to_th_iso(header.get("openingDate"))
            , kind="timestamp"),                                                                                      # 1.12
            "accountLevelMaturityDate": fill_null(athena_to_th_iso(account_level_maturity), kind="timestamp"),           # 1.13

            # balance/
            "lastLedgerBalanceAmount": to_amount(header.get("lastLedgerBalanceAmount")),         # 1.14
            "lastLedgerBalanceCurrency": fill_null(header.get("lastLedgerBalanceCurrency")),                # 1.15
            "lastAvailableBalanceAmount": to_amount(header.get("lastAvailableBalanceAmount")),   # 1.16
            "lastAvailableBalanceCurrency": fill_null(header.get("lastAvailableBalanceCurrency")),          # 1.17

            "startDateTime": fill_null(iso_to_th_iso(body.get("fromBookingDateTime")), kind="timestamp"),                # 1.18
            "endDateTime": fill_null(iso_to_th_iso(body.get("toBookingDateTime")), kind="timestamp"),                    # 1.19
            "numberOfTotalItems": len(statement_entries),                               # 1.20
            "statementDescription": "",                                                 # 1.21
            "creditLimit": to_amount(header.get("creditLimit")),                # 1.22
            "homeBranch": fill_null(select_by_language(                                           # 1.23
                language=language,
                th_value=header.get("homeBranch"),
                en_value=header.get("homeBranchEn"),
            )),
            "statementEntries": statement_entries,                                      # 1.24
        }




OPERATION_CLASS = CustomAPIOperation
