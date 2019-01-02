<?php  if ( ! defined('BASEPATH')) exit('No direct script access allowed');
 
class Main extends CI_Controller {
 
function __construct()
{
        parent::__construct();

/* Standard Libraries of codeigniter are required */
$this->load->database();
$this->load->helper('url');
/* ------------------ */ 
 
$this->load->library('grocery_CRUD'); 
 
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
		'Lead Skill' => array('ts_seq_leader', 'skill_list', 'ts_desc_us_calculated'),
		'Active' => array('ts_seq_skill', 'skill_list', 'ts_desc_us_calculated')
	);
    $this->_do_table('monster_list', $columns, $relations);
}

public function monster_info_list(){
	$columns = array('monster_no','tsr_seq','on_kr','on_us','pal_egg','rare_egg','fodder_exp','sell_price','history_jp','history_kr','history_us','tstamp');
	$relations = array(
		'Monster' => array('monster_no', 'monster_list', '[{monster_no}] {tm_name_us}'),
		'Series' => array('tsr_seq', 'series_list', 'name_us', array('del_yn' => false))
	);
    $this->_do_table('monster_info_list', $columns, $relations);
}

public function series_list(){
	$columns = array('tsr_seq','name_jp','name_kr','name_us','search_data','del_yn','tstamp');
	$order = array('del_yn', 'asc');
    $this->_do_table('series_list', $columns, null, $order);
}

public function dungeon_list(){
	$columns = array('dungeon_seq','order_idx','tdt_seq','dungeon_type','icon_seq','name_jp','name_kr','name_us','comment_jp','comment_kr','comment_us','show_yn','tstamp');
	$order = array('show_yn', 'asc');
    $this->_do_table('dungeon_list', $columns, null, $order);
}

public function csv_select(){
	$error = array('error' => '');
	$this->load->view('csv_select', $error);
}
public function csv_upload(){
	$config['upload_path'] = 'assets/uploads/';
	$config['allowed_types'] = 'csv';
	$config['file_name'] = 'tmp_import.csv';
	$config['overwrite'] = True;

	$this->load->library('upload', $config);

	if (!$this->upload->do_upload('userfile')){
		$error = array('error' => $this->upload->display_errors());
		$this->load->view('csv_select', $error);
	}else{
		$data = array('upload_data' => $this->upload->data());
		$this->load->view('csv_import', $data);
	}
}

public function _do_table($table = null, $columns = null, $relations = null, $order = null) {
	$crud = new grocery_CRUD();
    $crud->set_theme('flexigrid');
	$crud->set_table($table);

	if(!is_null($columns)){
		$crud->columns($columns);
		$crud->fields($columns);
	}
	if(!is_null($relations)){
	foreach($relations as $name => $r){
		$crud->display_as($r[0], $name);
		$crud->set_relation(...$r);
	}
	}
	if(!is_null($order)){
		$crud->order_by(...$order);
	}

    $crud->callback_before_insert(array($this,'_update_tstamp'));
    $crud->callback_before_update(array($this,'_update_tstamp'));

    $output = $crud->render();
    $this->load->view('padguide.php',$output);
}

function _update_tstamp($post_array,
 $primary_key) {
    $post_array['tstamp'] = time() * 1000;
    return $post_array;
}

} /* End main */
