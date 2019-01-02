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
</style>
</head>
<body>
<!-- Beginning header -->
    <div>
        <a href='<?php echo site_url('main/monster_list')?>'>Monster</a> | 
        <a href='<?php echo site_url('main/monster_info_list')?>'>Monster Info</a> | 
        <a href='<?php echo site_url('main/series_list')?>'>Series</a> | 
        <a href='<?php echo site_url('main/dungeon_list')?>'>Dungeon</a> | 
        <a href='<?php echo site_url('main/csv_upload')?>'>Import CSV</a>
    </div>
<!-- End of header-->

<?php echo $error;?>

<?php echo form_open_multipart('Main/csv_upload');?>

<input type="file" name="userfile" size="20" />

<br /><br />

<input type="submit" value="upload" />

</form>

</body>
</html>
