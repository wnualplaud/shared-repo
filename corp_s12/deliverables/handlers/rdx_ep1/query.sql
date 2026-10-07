SELECT 

        institutionName
    ,   accountId
    ,   accountSubType
    ,   accountStatus
    ,   accountNameEn
    ,   accountName

FROM rdx<env>_tbl1
WHERE citizenId = ?
    AND begins_with(accountKey, ?)

