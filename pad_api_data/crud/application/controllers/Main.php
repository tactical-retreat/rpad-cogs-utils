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
    $this->_do_table('monster_list');
}

public function monster_info_list(){
    $this->_do_table('monster_info_list');
}

public function series_list(){
    $this->_do_table('series_list');
}

public function dungeon_list(){
    $this->_do_table('dungeon_list');
}

public function _do_table($table = null) {
    $crud = new grocery_CRUD();
    $crud->set_theme('flexigrid');
    $crud->set_table($table);

    $crud->callback_before_insert(array($this, '_update_tstamp'));
    $crud->callback_before_update(array($this, '_update_tstamp'));

    $output = $crud->render();
    $this->load->view('padguide.php',$output);    
}

function _update_tstamp($post_array, $primary_key) {
    $post_array['tstamp'] = time() * 1000;
    return $post_array;
}

} /* End main */
