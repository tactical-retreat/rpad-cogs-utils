<?php
	function fix_table_name($tbl_name) {
	    $pieces = preg_split('/(?=[A-Z])/', $tbl_name);
	    $name = $pieces[0];
	    for ($x = 1; $x < count($pieces); $x++) {
	        $name = $name . '_' . strtolower($pieces[$x]);
	    }
	    return $name;
	}

	function serve($tbl_name, $args = []) {
		$base_path = "/home/tactical0retreat/rpad-cogs-utils/pad_api_data";
		$script = $base_path . "/serve_padguide_data.py";
		$db_config = $base_path . "/db_config.json";
		
		$cmd = "python3 " . $script . " --db_config=" . $db_config . " --db_table=" . $tbl_name;
		if (array_key_exists("data", $_POST)) {
			$data_arg = $_POST["data"];
			$cmd = $cmd . " --data_arg=" . $data_arg;
		}
		
		if (array_key_exists('no_items', $args)) {
			$cmd = $cmd . " --no_items";
		}
		
		if (array_key_exists('map_key', $args)) {
			$cmd = $cmd . " --map_key=" . $args['map_key'];
			$cmd = $cmd . " --map_value=" . $args['map_value'];
		}
		
		if (array_key_exists("plain", $_GET)) {
			$cmd = $cmd . " --plain";
		}
		
		passthru($cmd, $err);
	}
	
	
	function serve_plain($file_path) {
		$base_path = "/home/tactical0retreat/rpad-cogs-utils/pad_api_data";
		$script = $base_path . "/serve_padguide_data.py";
		
		$cmd = "python3 " . $script . " --raw_file=" . $file_path;
		
		if (array_key_exists("plain", $_GET)) {
			$cmd = $cmd . " --plain";
		}
		
		passthru($cmd, $err);
	}
?>