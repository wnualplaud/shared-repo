SELECT 

        institutionName
    ,   accountId
    ,   accountSubType
    ,   accountStatus
    ,   accountNameEn
    ,   accountName

FROM rdx${env}_tbl1
WHERE citizenId = :citizen_id
    AND ownerType = 'INDIVIDUAL'
    AND accountOwner = 'SINGLE'
    AND accountStatus = 'ACTIVE'

