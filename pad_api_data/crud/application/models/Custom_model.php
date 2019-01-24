<?php
class Custom_model  extends grocery_CRUD_Model  {
    function db_relation_n_n_update($field_info, $post_data ,$main_primary_key)
    {
		$this->db->set($field_info->primary_key_alias_to_this_table, 0, FALSE);
    	$this->db->where($field_info->primary_key_alias_to_this_table, $main_primary_key);
    	if(!empty($post_data))
    		$this->db->where_not_in($field_info->primary_key_alias_to_selection_table , $post_data);
		$this->db->update($field_info->relation_table);
		$this->db->reset_query();

    	$counter = 0;
    	if(!empty($post_data))
    	{
    		foreach($post_data as $primary_key_value)
	    	{
				$where_array = array(
	    			$field_info->primary_key_alias_to_selection_table => $primary_key_value
	    		);

	    		$this->db->where($where_array);
				$count = $this->db->from($field_info->relation_table)->count_all_results();

				if($count == 0)
				{
					if(!empty($field_info->priority_field_relation_table)){
						$where_array[$field_info->priority_field_relation_table] = $counter;
					}else{
						$where_array[$field_info->primary_key_alias_to_this_table] = $main_primary_key;
					}

					$this->db->insert($field_info->relation_table, $where_array);
					log_message('debug', $this->db->last_query());

				}elseif(!empty($field_info->priority_field_relation_table))
				{
					$this->db->update($field_info->relation_table, array($field_info->priority_field_relation_table => $main_primary_key) , $where_array);
					log_message('debug', $this->db->last_query());
				}else{
					$this->db->update($field_info->relation_table, array($field_info->primary_key_alias_to_this_table => $main_primary_key) , $where_array);
					log_message('debug', $this->db->last_query());
				}

				$counter++;
	    	}
    	}
    }
}
