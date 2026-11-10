SELECT

        REPLACE(SUBSTR(CAST(ITEM.CREATE_DATE AS STRING), 1, 10), '-', '')        AS `TM_KEY`
    ,   CAST(CAST(CARD.RDXCUST_NO AS BIGINT) AS STRING)                              AS `RDXCUST_NO`
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
    ,   'o0'                                                                     AS `LINE`
    ,   CARD.RDXSRC_CODE                                                            AS `LINK_T_CODE`

    ,   SUBSTR(CAST(ITEM.CREATE_DATE AS STRING), 1, 10)                          AS `DL_DATA_DT`

FROM `${hivevar:tmp_db}`.`${hivevar:prefix}STOCK_ITEM` ITEM

    INNER JOIN `${hivevar:tmp_db}`.`${hivevar:prefix}CARD` CARD
        ON ITEM.RDXSRC_CODE = CARD.RDXSRC_CODE
       AND ITEM.CMS_COLL_ID = CARD.CMS_COLL_ID
