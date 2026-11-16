SELECT

        bookingDateTime
    ,   valueDateTime
    ,   subAccountLevelMaturityDate
    ,   domainCode
    ,   familyCode
    ,   subFamilyCode
    ,   proprietaryBankTransactionCode
    ,   proprietaryBankTransactionDescription
    ,   creditDebitIndicator
    ,   amount
    ,   amountCurrency
    ,   transactionId
    ,   transactionRef
    ,   transactionInformation
    ,   creditorAccountId
    ,   creditorAccountName
    ,   receivingInstitutionCode
    ,   receivingInstitutionName
    ,   debtorAccountId
    ,   debtorAccountName
    ,   sendingInstitutionCode
    ,   sendingInstitutionName
    ,   merchantName
    ,   merchantNameEn

FROM rdx${env}_db1.rdx_tbl3
WHERE data_dt BETWEEN :from_data_dt AND :to_data_dt
    AND src_stm_id = :src_stm_id
    AND bookingDateTime 
        BETWEEN from_iso8601_timestamp(:from_booking_dttm) 
        AND from_iso8601_timestamp(:to_booking_dttm)
    AND accountId = :account_id

ORDER BY bookingDateTime DESC, transactionId DESC
