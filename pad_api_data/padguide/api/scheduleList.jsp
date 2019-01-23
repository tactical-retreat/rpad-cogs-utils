<?php 
	require 'serve.php';
    $args = [
        'timelimit' => true,
    ];
    print(serve(fix_table_name(basename(__FILE__, '.jsp')), $args));
?>
