SELECT

        TRIM(TFILE.RDXSRCT_CODE)                                   AS RDXSRCT_CODE
    ,   TFILE.RDXSET_ID                                           AS RDXSET_ID

    ,   TRIM(CAST(RDXSET_SPC.COLL AS STRING))                     AS COLL
    ,   TRIM(RDXSET_SPC.CUST_RDXCUST)                                 AS CUST_RDXCUST

    ,   TFILE.DL_DATA_DT                                        AS DL_DATA_DT
    ,   CURRENT_TIMESTAMP()                                     AS DL_LOAD_TS

FROM `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_RDXSET_TFILE_INFO TFILE

    INNER JOIN `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_RDXSET_SPC RDXSET_SPC
        ON TFILE.RDXSET_ID = RDXSET_SPC.RDXSET_ID
       AND RDXSET_SPC.DL_DATA_DT = '${hivevar:dl_data_dt}'

WHERE TFILE.DL_DATA_DT = '${hivevar:dl_data_dt}'
