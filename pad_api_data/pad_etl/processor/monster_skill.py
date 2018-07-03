class MonsterItem(object):
    def __init__(self, merged_card_jp: MergedCard, merged_card_na: MergedCard):
        # Primary key, set later
        self.ts_seq = None
         
        # Not right but not useful either
        self.mag_atk = 0  
        self.mag_hp = 0
        self.mag_rcv = 0
        self.reduce_dmg = 
        
        # Not sure what this order is used for
        self.order_idx = 0
        
        # Used but not sure what for
        self.t_condition = 0

        # Seems (mostly) unused
        self.rta_seq_1 = None 
        self.rta_seq_2 = None
        self.ta_seq_1 = 0
        self.ta_seq_2 = 0
        self.tt_seq_1 = 0
        self.tt_seq_2 = 0
        
        # Useful fields        
        self.tstamp = int(time.time())
        self.ts_desc_jp = merged_card_jp.card.clean_description 
        self.ts_desc_kr = 'unknown_{}'.format(merged_card_jp.card.skill_id)
        self.ts_desc_us = merged_card_na.card.clean_description
        self.ts_name_jp = merged_card_jp.card.name
        self.ts_name_kr = 'unknown_{}'.format(merged_card_jp.card.skill_id)
        self.ts_name_us = merged_card_na.card.name
        self.turn_max = merged_card_jp.card.turn_max
        self.turn_min = merged_card_jp.card.turn_min
        
        self.search_data = '{} {}'.format(self.ts_name_jp, self.ts_name_us)

    def insert_sql(self):
        sql = """
        INSERT INTO `padguide`.`skill_list`
            (`mag_atk`,
            `mag_hp`,
            `mag_rcv`,
            `order_idx`,
            `reduce_dmg`,
            `rta_seq_1`,
            `rta_seq_2`,
            `search_data`,
            `ta_seq_1`,
            `ta_seq_2`,
            `tstamp`,
            `ts_desc_jp`,
            `ts_desc_kr`,
            `ts_desc_us`,
            `ts_name_jp`,
            `ts_name_kr`,
            `ts_name_us`,
            `ts_seq`,
            `tt_seq_1`,
            `tt_seq_2`,
            `turn_max`,
            `turn_min`,
            `t_condition`)
            VALUES
            ({mag_atk},
            {mag_hp},
            {mag_rcv},
            {order_idx},
            {reduce_dmg},
            {rta_seq_1},
            {rta_seq_2},
            {search_data},
            {ta_seq_1},
            {ta_seq_2},
            {tstamp},
            {ts_desc_jp},
            {ts_desc_kr},
            {ts_desc_us},
            {ts_name_jp},
            {ts_name_kr},
            {ts_name_us},
            {ts_seq},
            {tt_seq_1},
            {tt_seq_2},
            {turn_max},
            {turn_min},
            {t_condition});
        """
