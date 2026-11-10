SELECT DISTINCT

        TRIM(RDXSRCT_CODE)                                         AS RDXSRC_CODE
    ,   TRIM(CAST(COLL_ID AS STRING))                           AS CMS_COLL_ID
    ,   TRIM(RDXCUST_NO)                                            AS RDXCUST_NO

    ,   DL_DATA_DT                                              AS DL_DATA_DT
    ,   CURRENT_TIMESTAMP()                                     AS DL_LOAD_TS

FROM `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_RDXSET_IMP_SPC_CARD

WHERE DL_DATA_DT = '${hivevar:dl_data_dt}'

  AND COLL_ID IS NOT NULL
  AND TRIM(COLL_ID) <> ''
  AND LOWER(TRIM(COLL_ID)) <> 'null'

  AND RDXCUST_NO IS NOT NULL
  AND TRIM(RDXCUST_NO) <> ''
  AND LOWER(TRIM(RDXCUST_NO)) <> 'null'
