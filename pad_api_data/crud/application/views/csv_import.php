<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
<style type='text/css'>
body
{
    font-family: Arial;
    font-size: 14px;
}
a {
    color: blue;
    text-decoration: none;
    font-size: 14px;
}
a:hover
{
    text-decoration: underline;
}
.grid {
	display: grid;
	grid-template-rows: min-content;
}
.grid.table {
	grid-template-columns: min-content repeat(<?php echo isset($headings) ? sizeof($headings) : 0;?>, 1fr);
}
.grid.table > *{
	border-bottom: dotted 1px black;
	padding: 1px;
}
.grid.list {
	grid-template-columns: 1fr 2fr;
}
</style>
</head>
<body>
<!-- Beginning header -->
    <div>
        <a href='<?php echo site_url('main/monster_list')?>'>Monster</a> | 
        <a href='<?php echo site_url('main/monster_info_list')?>'>Monster Info</a> | 
        <a href='<?php echo site_url('main/series_list_active')?>'>Series</a> [<a href='<?php echo site_url('main/series_list_inactive')?>'>Deleted</a>] | 
        <a href='<?php echo site_url('main/dungeon_list_active')?>'>Dungeon</a> [<a href='<?php echo site_url('main/dungeon_list_inactive')?>'>Deleted</a>] | 
        <a href='<?php echo site_url('main/csv_upload')?>'>CSV Bulk Edit</a>
    </div>
<!-- End of header-->

<?php
if(isset($result_msg)){
	echo $result_msg;
	echo '<p>' . anchor('main/csv_upload', 'Upload Another File') . '</p>';
}
if(isset($error)){
	echo $error;
}
if(!isset($csv_data)):
	echo form_open_multipart('main/csv_upload');
?>

<input type="file" name="userfile" size="20" />

<br /><br />

<input type="submit" value="upload" />

</form>

<?php else:
echo form_open_multipart('main/csv_update');
?>
<div class="grid table">
<div><b>Use</b></div>

<?php
foreach($headings as $head){
	echo '<div><b>' . $head . '</b></div>';
}
foreach($csv_data as $i => $types){
	foreach($types as $type => $row){
		echo '<div>';
		echo '<label><input type="radio" name="action_row_' . $i . '" value="' . ($type == 'new' ? '1" checked' : '0"') . '>' . $type . ' values</label>';
		echo '</div>';
		foreach($row as $value){
			if(is_array($value)){
				echo '<div class="grid list">';
				foreach($value as $k => $v){
					echo '<div>[' . $k . ']</div>';
					echo '<div>' . $v . '</div>';
				}
			}else{
				echo '<div>';
				echo $value;
			}
			echo '</div>';
		}
	}
}
?>
</div>
<input type="submit" value="update"/>
</form>
<?php endif;?>

</body>
</html>