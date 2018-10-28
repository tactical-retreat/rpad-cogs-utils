<?php 
	require 'serve.php';
    print(serve(fix_table_name(basename(__FILE__, '.jsp'))));
?>
