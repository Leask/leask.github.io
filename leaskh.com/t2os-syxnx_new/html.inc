<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>Tw2other</title>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <style type="text/css">
      img {border-width: 0}
      * {font-family:'Lucida Grande', sans-serif;}
    </style>
  </head>
  <body>
    <div>
      <h2>Tw2other</h2>

      <p>清除认证：<a href='./clearsessions.php'>clearing your session</a>.</p>
	
      <p>
       如果有问题，可以联系Tw2other作者 :@<a href="http://twitter.com/cluries">cluries</a>
      </p>
      <p>
      	感谢twitter oauth lib的作者  @<a href='http://twitter.com/abraham'>abraham</a>
      </p>
      <P>
       	<a href="http://dev.twitter.com/apps/new">注册新的Application</a>
      </P>
      	<p>
      	注意，在Twitter注册Application的时候，Application Type这一项要选中Browser <br />
      	Application Type这一项选中Browser后，Callback URL这里面填写你自己tw2other里面callback.php的URL
      	</p>
      <hr />
      <?php if (isset($menu)) { ?>
        <?php echo $menu; ?>
      <?php } ?>
    </div>
    <?php if (isset($status_text)) { ?>
      <?php echo '<h3>'.$status_text.'</h3>'; ?>
    <?php } ?>
    <p>
      <pre>
        <?php print_r($content); ?>
      </pre>
    </p>

  </body>
</html>
