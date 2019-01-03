<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
 
<?php 
foreach($css_files as $file): ?>
    <link type="text/css" rel="stylesheet" href="<?php echo $file; ?>" />
 
<?php endforeach; ?>
<?php foreach($js_files as $file): ?>
 
    <script src="<?php echo $file; ?>"></script>
<?php endforeach; ?>
 
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
    <div style='height:20px;'></div>  
    <div>
<?php echo $output; ?>
 
    </div>
<!-- Beginning footer -->
<div><!-- Footer --></div>
<!-- End of Footer -->
</body>
</html>
