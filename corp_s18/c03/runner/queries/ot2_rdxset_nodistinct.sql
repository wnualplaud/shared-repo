SELECT

        REPLACE(SUBSTR(CAST(ITEM.CREATE_DATE AS STRING), 1, 10), '-', '')        AS `TM_KEY`
    ,   CAST(CAST(CARD.RDXCUST_NO AS BIGINT) AS STRING)                             AS `RDXCUST_NO`
    ,   ITEM.PRODUCT_DESC                                                        AS `PRODUCT_DESC`
    ,   CAST(ITEM.TOTAL_AMOUNT AS DECIMAL(20, 2))                                AS `VALUE`
    ,   CAST(ITEM.UNIT_AMOUNT  AS DECIMAL(20, 4))                                AS `QTY`
    ,   CAST(ITEM.UNIT_PRICE   AS DECIMAL(20, 4))                                AS `PRICE`
    ,   DATE_FORMAT(CAST(ITEM.SURVEY_DATE AS TIMESTAMP), 'yyyyMMdd')
                                                                                 AS `SURVEY_DATE`
    ,   ITEM.OS_SURVEYER_NAME                                                    AS `SURVEYOR_NM`
    ,   ITEM.SPC_SURPRISE_CHECK                                                  AS `SURPRISE_FLAG`
    ,   ITEM.REP_CODE                                                            AS `RDXSRC_ID`

    ,   ITEM.RDXSRC_ID                                                              AS `SRC_RDXSRC_ID`
    ,   ITEM.RDXSRC_CODE                                                            AS `SRC_RDXSRC_CODE`
    ,   ITEM.REP_CODE                                                            AS `SRC_REP_CODE`
    ,   ITEM.RDXSRC_COLL_ID                                                         AS `SRC_RDXSRC_COLL_ID`
    ,   ITEM.RDXSRC_COLL_ITEM_ID                                                    AS `SRC_RDXSRC_COLL_ITEM_ID`
    ,   ITEM.COLL_SPC_NO                                                         AS `SRC_COLL_SPC_NO`

    ,   ITEM.REQUEST_OFFICE_CODE                                                 AS `SRC_REQUEST_OFFICE_CODE`
    ,   ITEM.RDXBANK_GRP_CODE                                                        AS `SRC_RDXBANK_GRP_CODE`

    ,   CURRENT_TIMESTAMP()                                                      AS `DL_LOAD_TS`
    ,   'ot2'                                                                    AS `LINE`
    ,   RDXSET_T.RDXSRCT_CODE                                                           AS `LINK_T_CODE`

    ,   SUBSTR(CAST(ITEM.CREATE_DATE AS STRING), 1, 10)                          AS `DL_DATA_DT`

FROM `${hivevar:tmp_db}`.`${hivevar:prefix}STOCK_ITEM` ITEM

    INNER JOIN `${hivevar:tmp_db}`.`${hivevar:prefix}RDXSET_T` RDXSET_T
        ON ITEM.RDXSRC_CODE = RDXSET_T.RDXSRCT_CODE
       AND ITEM.CMS_COLL_ID = RDXSET_T.COLL

    INNER JOIN (

        SELECT

                TRIM(RDXSRCT_CODE)                                 AS RDXSRCT_CODE
            ,   RDXSET_ID                                         AS RDXSET_ID
            ,   TRIM(CAST(COLL_ID AS STRING))                   AS COLL_ID
            ,   TRIM(RDXCUST_NO)                                    AS RDXCUST_NO

        FROM `${hivevar:environment}_PERSIST_RDXSRC_DB`.RDXSRC_TBL_RDXSRC_RDXSET_IMP_SPC_CARD

        WHERE DL_DATA_DT = '${hivevar:dl_data_dt}'

          AND COLL_ID IS NOT NULL
          AND TRIM(COLL_ID) <> ''
          AND LOWER(TRIM(COLL_ID)) <> 'null'

          AND RDXCUST_NO IS NOT NULL
          AND TRIM(RDXCUST_NO) <> ''
          AND LOWER(TRIM(RDXCUST_NO)) <> 'null'

    ) CARD
        ON RDXSET_T.RDXSRCT_CODE = CARD.RDXSRCT_CODE
       AND RDXSET_T.RDXSET_ID = CARD.RDXSET_ID
       AND RDXSET_T.COLL = CARD.COLL_ID
       AND RDXSET_T.CUST_RDXCUST = CARD.RDXCUST_NO
