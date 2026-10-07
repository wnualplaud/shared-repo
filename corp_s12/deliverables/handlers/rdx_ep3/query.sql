
SELECT 

        accountId
    ,   lastLedgerBalanceAmount
    ,   lastLedgerBalanceCurrency
    ,   lastAvailableBalanceAmount
    ,   lastAvailableBalanceCurrency
    ,   creditLimit

FROM rdx<env>_tbl2
WHERE accountId = ?
    AND accountSubType = ?

