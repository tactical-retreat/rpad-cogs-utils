<html>
<head>
<title>Upload Form</title>
</head>
<body>

<h3>Your file was successfully uploaded!</h3>

<?php
$csv = array_map('str_getcsv', file($upload_data['full_path']));
print_r($csv);
?>

<p><?php echo anchor('csv_select', 'Upload Another File!'); ?></p>

</body>
</html>