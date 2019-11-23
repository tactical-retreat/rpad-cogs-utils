<?php  if ( ! defined('BASEPATH')) exit('No direct script access allowed');
 
class Main extends CI_Controller {
public $csv_primary_key = 'monster.monster_id';
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
$this->monsters();
}

public function list()
{
echo "<pre>";
print_r($this->db->list_tables());
die();
}

public function monsters(){
	$columns = array(
	//monster no
	'monster_id','monster_no_jp','monster_no_kr','monster_no_na',
	//name
	'name_jp','name_kr','name_na','name_na_override',
	//stats
	'rarity','cost','level','exp','hp_max','atk_max','rcv_max','limit_mult',
	//relations
	'attribute_1_id','attribute_2_id','type_1_id','type_2_id','type_3_id','active_skill_id', 'leader_skill_id','series_id',
	//misc
	'reg_date','tstamp'
	);
	$relations = array(
		'Main Att' => array('attribute_1_id', 'd_attributes', 'name'),
		'Sub Att' => array('attribute_2_id', 'd_attributes', 'name'),
		'Type 1' => array('type_1_id', 'd_types', 'name'),
		'Type 2' => array('type_2_id', 'd_types', 'name'),
		'Type 3' => array('type_3_id', 'd_types', 'name'),
		'Series' => array('series_id', 'series', 'name_na'),
		# 'Lead Skill' => array('leader_skill_id', 'leader_skills', '{leader_skill_id} - {desc_na}'),
		# 'Active' => array('active_skill_id', 'active_skills', '{active_skill_id} - {desc_na}')
	);
    $this->_do_table('monsters', $columns, $relations);
}

public function series(){
	$columns = array('series_id','name_jp','name_kr','name_na','tstamp');
	$relations = array(
		//ordering looks nice but is slow af
		# 'N2N_series_monsters' => array('series_monsters', 'monsters', 'monsters', 'series_id','monster_id','name_na'/*, 'monster_no asc'*/)
		'monsters' => array('series_id', 'monsters', 'series_id')
	);
    $this->_do_table('series', $columns, $relations, null);
}

public function dungeons_active(){
	$columns = array('dungeon_id','name_na','name_jp','dungeon_type','icon_id','reward_na','reward_icon_ids','visible','tstamp');
	$filter = array('visible', 1);
    $this->_do_table('dungeons', $columns, null, $filter);
}

public function dungeons_inactive(){
	$columns = array('dungeon_id','name_na','name_jp','dungeon_type','icon_id','reward_na','reward_icon_ids','visible','tstamp');
	$filter = array('visible', 0);
    $this->_do_table('dungeons', $columns, null, $filter);
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
						
						if($fieldname == 'name_us_override'){
							$this->db->select($fieldname . ', name_us, name_jp, ' . $wherefield);
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

    $crud->unset_texteditor('name_na', 'name_jp', 'name_kr', 'name_na_override');

    $crud->callback_before_insert(array($this,'_update_tstamp'));
    $crud->callback_before_update(array($this,'_update_tstamp'));

    $output = $crud->render();
    $this->load->view('padguide.php', $output);
}

function _update_tstamp($post_array,
 $primary_key) {
    $post_array['tstamp'] = time();
    return $post_array;
}

} /* End main */
