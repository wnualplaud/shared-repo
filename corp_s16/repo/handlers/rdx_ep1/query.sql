SELECT 

        institutionName
    ,   accountId
    ,   accountSubType
    ,   accountStatus
    ,   accountNameEn
    ,   accountName

FROM rdx${env}_tbl1
WHERE citizenId = :citizen_id
    AND begins_with(accountKey, :key_prefix)
    AND ownerType = 'INDIVIDUAL'
    AND accountOwner = 'SINGLE'
    AND accountStatus = 'ACTIVE'

