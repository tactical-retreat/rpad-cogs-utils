<?php  if ( ! defined('BASEPATH')) exit('No direct script access allowed');
 
class Main extends CI_Controller {
public $csv_primary_key = 'monster_list.monster_no';
function __construct()
{
        parent::__construct();

/* Standard Libraries of codeigniter are required */
$this->load->database();
$this->load->helper('url');
/* ------------------ */ 
 
$this->load->library('grocery_CRUD'); 
$this->load->library('upload');
$this->load->driver('cache', array('adapter' => 'apc', 'backup' => 'file'));
}
 
public function index()
{
$this->monster_list();
}

public function list()
{
echo "<pre>";
print_r($this->db->list_tables());
die();
}

public function monster_list(){
	$columns = array(
	//monster no
	'monster_no','monster_no_jp','monster_no_kr','monster_no_us',
	//name
	'tm_name_jp','tm_name_kr','tm_name_us','tm_name_us_override','pronunciation_jp',
	//stats
	'rarity','cost','level','exp','hp_min','hp_max','atk_min','atk_max','rcv_min','rcv_max','limit_mult','ratio_atk','ratio_hp','ratio_rcv',
	//relations
	'ta_seq','ta_seq_sub','tt_seq','tt_seq_sub','ts_seq_leader','ts_seq_skill',
	//comments
	'comment_jp','comment_kr','comment_us',
	//misc
	'reg_date','tstamp'
	/* Not displayed
	app_version: probably useless
	te_seq: redundant with exp
	*/
	);
	$relations = array(
		'Main Att' => array('ta_seq', 'attribute_list', 'ta_name_us'),
		'Sub Att' => array('ta_seq_sub', 'attribute_list', 'ta_name_us'),
		'Type 1' => array('tt_seq', 'type_list', 'tt_name_us'),
		'Type 2' => array('tt_seq_sub', 'type_list', 'tt_name_us'),
		'Lead Skill' => array('ts_seq_leader', 'skill_list', '{ts_seq} - {ts_desc_us_calculated}'),
		'Active' => array('ts_seq_skill', 'skill_list', '{ts_seq} - {ts_desc_us_calculated}')
	);
    $this->_do_table('monster_list', $columns, $relations);
}

public function monster_info_list(){
	$columns = array('monster_no','tsr_seq','on_kr','on_us','pal_egg','rare_egg','fodder_exp','sell_price','history_jp','history_kr','history_us','tstamp');
	$relations = array(
		'Monster' => array('monster_no', 'monster_list', '{monster_no} - {tm_name_us}'),
		'Series' => array('tsr_seq', 'series_list', '{tsr_seq} - {name_us}', array('del_yn' => false))
	);
    $this->_do_table('monster_info_list', $columns, $relations);
}

public function series_list_active(){
	$columns = array('tsr_seq','monsters','name_jp','name_kr','name_us','search_data','del_yn','tstamp');
	$filter = array('del_yn', 0);
	$relations = array(
		//ordering looks nice but is slow af
		'N2N_monsters' => array('monsters', 'monster_info_list', 'monster_list', 'tsr_seq', 'monster_no' , 'tm_name_us'/*, 'monster_no asc'*/)
	);
    $this->_do_table('series_list', $columns, $relations, $filter);
}

public function series_list_inactive(){
	$columns = array('tsr_seq','name_jp','name_kr','name_us','search_data','del_yn','tstamp');
	$filter = array('del_yn', 1);
    $this->_do_table('series_list', $columns, null, $filter);
}

public function dungeon_list_active(){
	$columns = array('dungeon_seq','order_idx','tdt_seq','dungeon_type','icon_seq','name_jp','name_kr','name_us','comment_jp','comment_kr','comment_us','show_yn','tstamp');
	$filter = array('show_yn', 1);
    $this->_do_table('dungeon_list', $columns, null, $filter);
}

public function dungeon_list_inactive(){
	$columns = array('dungeon_seq','order_idx','tdt_seq','dungeon_type','icon_seq','name_jp','name_kr','name_us','comment_jp','comment_kr','comment_us','show_yn','tstamp');
	$filter = array('show_yn', 0);
    $this->_do_table('dungeon_list', $columns, null, $filter);
}

private function _get_primary_key($tablename){
	$f_dat = $this->db->field_data($tablename);
	foreach ($f_dat as $f){
		if($f->primary_key == 1){
			return $f->name;
		}
	}
	return '';
}

public function csv_upload(){
	$output = array();
	if (!$this->upload->do_upload('userfile')){
		$output['error'] = $this->upload->display_errors();
	}else{
		$upload_data = $this->upload->data();
		if (($handle = fopen($upload_data['full_path'], 'r')) !== false) {
			$filesize = filesize($upload_data['full_path']);
			$output['csv_data'] = array();
			$pk_idx = null;
			$fields = array();
			$output['headings'] = array();
			while (($data = fgetcsv($handle, $filesize, ',')) !== false) {
				if(!isset($pk_idx)) {
					if(!in_array($this->csv_primary_key, $data)){
						$output['error'] = '<p>Missing ' . $this->csv_primary_key . ' field</p>';
						break;
					}
					$pk_idx = array_search($this->csv_primary_key, $data);
					$output['headings'] = $data;
					$fields[$pk_idx] = explode('.', $this->csv_primary_key, 2);
					$pk_fieldname = $fields[$pk_idx][1];
					foreach($data as $i => $d){
						if($i == $pk_idx){
							continue;
						}
						$tmp = explode('.', $d, 2);
						if(sizeof($tmp) < 2){
							$output['error'] = '<p>' . $d . ' not in <table>.<field> format</p>';
							break;
						}
						if(in_array($fields[$pk_idx][1], $this->db->list_fields($tmp[0]))){
							$tmp[2] = $pk_fieldname;
						}else{
							$tmp[2] = $tmp[1];
							$tmp[1] = $this->_get_primary_key($tmp[0]);
						}
						$fields[$i] = $tmp;
					}
				} else {
					if($data[$pk_idx] == ''){
						continue;
					}
					$pk_tablename = $fields[$pk_idx][0];
					$pk_fieldname = $fields[$pk_idx][1];
					$this->db->select($pk_fieldname);
					$this->db->from($pk_tablename);
					$this->db->where($pk_fieldname, $data[$pk_idx]);
					$res = $this->db->get();
					if($res->num_rows() == 0){
						$output['error'] = '<p>' . $data[$pk_idx] . ' does not exist in ' . $this->csv_primary_key . '</p>';
						continue;
					}
					
					$input_data = array($this->csv_primary_key => $data[$pk_idx]);
					$db_data = array($this->csv_primary_key => $data[$pk_idx]);
					foreach($fields as $i => $field){
						if($i == $pk_idx){
							continue;
						}
						$tablename = $field[0];
						$fieldname = $field[1];
						$wherefield = $field[2];
						$heading = $output['headings'][$i];
						if($wherefield == $pk_fieldname){
							$whereinput = $data[$pk_idx];
						}else{
							$whereinput = $data[$i];
						}
						if(!array_key_exists($heading, $input_data)){
							$input_data[$heading] = $data[$i];
						}
						
						if($fieldname == 'tm_name_us_override'){
							$this->db->select($fieldname . ', tm_name_us, tm_name_jp, ' . $wherefield);
						}else{
							$this->db->select($fieldname . ', ' . $wherefield);
						}
						$this->db->from($tablename);
						$this->db->where($wherefield, $whereinput);						
						$res = $this->db->get();
						//echo $this->db->last_query() . '<br/>';
						if($res->num_rows() == 0){
							$db_data[$heading] = 'null';
						}else{
							$row = $res->row_array();
							unset($row[$tablename . '.' . $pk_fieldname]);
							unset($row[$pk_fieldname]);
							if(sizeof($row) == 1){
								$row = reset($row);
							}
							$db_data[$heading] = $row;
							if($wherefield != $pk_fieldname){
								$insert_idx = array_search($fieldname, array_column($fields, 1));
								if($insert_idx != false){
									$input_data[$output['headings'][$insert_idx]] = $row[$fieldname];
								}
							}
						}
					}
					$output['csv_data'][] = array('new' => $input_data, 'current' => $db_data);
				}
			}
			fclose($handle);
			unlink($upload_data['full_path']);
			//30 min expiry
			if(!$this->cache->get('csv_data')){
				$this->cache->save('csv_data', $output['csv_data'], 1800);
			}
		}
	}
	$this->load->view('csv_import', $output);
}
public function csv_update(){
	$i = 0;
	$output = array();
	$csv_data = $this->cache->get('csv_data');
	if(!$csv_data){
		$output['error'] = 'Cache miss, please upload again';
	}else{
		$complete = array();
		$tmp = explode('.', $this->csv_primary_key, 2);
		$pk_tablename = $tmp[0];
		$pk_fieldname = $tmp[1];
		while(array_key_exists('action_row_' . $i, $_POST)){
			if($_POST['action_row_' . $i] == true){
				$by_table = array();
				$pk_value = null;
				foreach($csv_data[$i]['new'] as $key => $value){
					if($key == $this->csv_primary_key){
						$pk_value = $value;
						continue;
					}
					if(strlen($value) == 0){
						continue;
					}
					$tmp = explode('.', $key, 2);
					if(!in_array($pk_fieldname, $this->db->list_fields($tmp[0]))){
						continue;
					}
					if(!array_key_exists($tmp[0], $by_table)){
						$by_table[$tmp[0]] = array();
					}

					$by_table[$tmp[0]][$tmp[1]] = $value;
				}
				//print_r($by_table);
				//echo '<br/>';
				foreach($by_table as $table => $data){
					$this->db->where($pk_fieldname, $pk_value);
					$this->db->update($table, $data);
					//echo $this->db->last_query();
					//echo '<br/>';
					$complete[] = $pk_value;
				}
			}
			$i++;
		}
		$csv_data = $this->cache->delete('csv_data');
		$output['result_msg'] = sizeof($complete) > 0 ? '<p>Updated ' . print_r($complete, true) . '</p>' : '<p>No changes made</p>';
	}
	$this->load->view('csv_import', $output);
}
public function _do_table($table = null, $columns = null, $relations = null, $filter = null, $order = null) {
	$crud = new grocery_CRUD();
    $crud->set_theme('flexigrid');
	$crud->set_model('Custom_model');
	$crud->set_table($table);

	if(!is_null($columns)){
		$crud->columns($columns);
		$crud->fields($columns);
	}
	if(!is_null($relations)){
		foreach($relations as $name => $r){
			if(strpos($name, 'N2N') === 0){
				$crud->set_relation_n_n(...$r);
			}else{
				$crud->display_as($r[0], $name);
				$crud->set_relation(...$r);
			}
		}
	}
	if(!is_null($filter)){
		$crud->where(...$filter);
	}
	if(!is_null($order)){
		$crud->order_by(...$order);
	}

    $crud->callback_before_insert(array($this,'_update_tstamp'));
    $crud->callback_before_update(array($this,'_update_tstamp'));

    $output = $crud->render();
    $this->load->view('padguide.php', $output);
}

function _update_tstamp($post_array,
 $primary_key) {
    $post_array['tstamp'] = time() * 1000;
    return $post_array;
}

} /* End main */
