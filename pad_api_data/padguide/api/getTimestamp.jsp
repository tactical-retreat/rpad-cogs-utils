<?php 
	require 'serve.php';
	$args = [
		'map_key' => 'table',
		'map_value' => 'tstamp'
	]
    print(serve(fix_table_name(basename(__FILE__, '.jsp')), $args));
?>
