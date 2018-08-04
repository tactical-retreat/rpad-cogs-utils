<?php
	function fix_table_name($tbl_name) {
	    $pieces = preg_split('/(?=[A-Z])/', $tbl_name);
	    $name = $pieces[0];
	    for ($x = 1; $x <= count(pieces); $x++) {
	        $name = $name . '_' . strtolower($pieces[$x]);
	    }
	    return $name;
	}

	function serve($tbl_name, $no_items = false) {
		$base_path = "/home/tactical0retreat/rpad-cogs-utils/pad_api_data";
		$script = $base_path . "/serve_padguide_data.py";
		$db_config = $base_path . "/db_config.json";
		
		$cmd = "python3 " . $script . " --db_config=" . $db_config . " --db_table=" . $tbl_name;
		$data_arg = $_POST["data"];
		if ($data_arg != "") {
			$cmd = $cmd . " --data_arg=" . $data_arg;
		}
		
		if ($no_items) {
			$cmd = $cmd . " --no_items";
		}
		
		$plain = $_POST["plain"];
		if ($plain = "true") {
			$cmd = $cmd . " --plain";
		}
		
		passthru($cmd, $err);
	}
	
	
	function serve_plain($file_path) {
		$base_path = "/home/tactical0retreat/rpad-cogs-utils/pad_api_data";
		$script = $base_path . "/serve_padguide_data.py";
		
		$cmd = "python3 " . $script . " --raw_file=" . $file_path;
		
		$plain = $_POST["plain"];
		if ($plain = "true") {
			$cmd = $cmd . " --plain=";
		}
		
		passthru($cmd, $err);
	}
?>