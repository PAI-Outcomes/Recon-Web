require "D:/WWW/www.tdsdna.com/cgi-bin/common.pl";
require "D:/RedeemRx/MyData/vars.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;
use DBI;

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$PH_ID      = $in{'fname'};
$USER       = $in{'lname'};
$Agg_String = $in{'Agg_String'};

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);
#______________________________________________________________________________

my %times = (
  "20220228:1000" => "Monday, February 28th at 10am CST",
  "20220228:1400" => "Monday, February 28th at 2pm CST",
  "20220304:1400" => "Friday, March 4th at 2pm CST",
  "20220307:1000" => "Monday, March 7th at 10am CST",
  "20220307:1400" => "Monday, March 7th at 2pm CST",
  "20220224:1000" => "Thursday, February 24th at 10am CST",
  "20220224:1400" => "Thursday, February 24th at 2pm CST",
  "20220225:1000" => "Friday, February 25th at 10am CST",
  "20220225:1400" => "Friday, February 25th at 2pm CST",
  "20220301:1000" => "Tuesday, March 1st at 10am CST",
  "20220301:1400" => "Tuesday, March 1st at 2pm CST",
  "20220302:1000" => "Wednesday, March 2nd at 10am CST",
  "20220302:1400" => "Wednesday, March 2nd at 2pm CST",
  "20220303:1000" => "Thursday, March 3rd at 10am CST",
  "20220303:1400" => "Thursday, March 3rd at 2pm CST",
  "20220304:1000" => "Friday, March 4th at 10am CST",
  "20220308:1000" => "Tuesday, March 8th at 10am CST",
  "20220308:1400" => "Tuesday, March 8th at 2pm CST"
);

#______________________________________________________________________________

print <<EOF;
Content-type: text/html\n\n
<!doctype html> 
<html lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=1024" />
  
  <TITLE>ReconRx Webinar</TITLE>

  <link rel="stylesheet" href="../css/TDS_Style.css?ver=1.2" />  

  <script src="https://code.jquery.com/jquery-1.11.1.min.js"></script>
  
  <meta name="viewport" content="width=device-width, initial-scale=1">

</head>

<body leftmargin="0" topmargin="0" marginwidth="0" marginheight="0">

<div id="header">
        <div style="padding-bottom: 10px; display: block; width: 100%;"><a href="https://www.tdsclinical.com/"><img id="main_logo" src="../images/TDSlogo.png" alt="TDS Clinical" title=""></a></div>
</div>

<div class='main_body'>

	<!-- <img id="image_top" src="../images/adults-business-coffee-webinar.jpg" alt="TDS Clinical" title=""> -->
	<img id="image_top" src="../images/Shiny_blue_wave_background3.png" alt="TDS Clinical" title="">

EOF

#______________________________________________________________________________

$DBNAME   = 'ReconRxDB';
$TABLE    = 'register';

$dbx = DBI->connect("DBI:mysql:$DBNAME:$dbhost",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

$return = &add_registry();

&display_webpage($return);

&email_ram();

print "</div>\n</body>\n</html>";

$dbx->disconnect;

exit(0);

#______________________________________________________________________________

sub add_registry {
  my $retval = 1;
  my $fname =  "$in{'fname'}";
  my $lname =  "$in{'lname'}"; 
  my $ncpdp =  "$in{'ncpdp'}";
  my $pharm =  "$in{'pharmacy_name'}"; 
  my $sw    =  "$in{'software'}";
  my $email =  "$in{'email'}";
  my $phone =  "$in{'phone'}";
  my $time  =  "$in{'time_sel'}";

  my $sth = $dbx->prepare("INSERT INTO $DBNAME.$TABLE (fname, lname, ncpdp, pharmacy_name, software, email, phone, time_sel)
             VALUES (?,?,?,?,?,?,?,?)");

#  print "SQL: $sql<br>";
##  $retval = $dbx->do($sql) or die $DBI::errstr;  
$sth->execute("$fname", "$lname", "$ncpdp", "$pharm","$sw", "$email", "$phone", "$time");
  return($retval);
}

#______________________________________________________________________________

sub display_webpage {

print <<EOL;
	<div class='signup_body'>
		<img id="signup_img" src="../images/ReconRX_LogoWTag_SM.jpg" alt="ReconRx" title="">
		<p style='text-align: center; font-weight: bold;'>You have successfully registered for the ReconRx Reconciliation Webinar on:</p>
                <p style='text-align: center; font-size: 18px; color: #063970; font-weight: bold;'>$in{'time_sel'}</p>
		<p style='text-align: center;'>Again, thank you for your interest in attending a ReconRx Reconciliation Webinar and we look forward to meeting you!</p>
                <hr>
		<p style='text-align: center; font-weight: bold;'>Webinar login information will be sent to you shortly from <span style='color: #5FC8ED;'>apritchard\@tdsclinical.com</span>.</p>
	</div>
EOL
}

#______________________________________________________________________________

sub email_ram {
  my $from = "NoReply";

#  $to = 'bprowell@tdsclinical.com';
##  $to = 'sdowning@tdsclinical.com';
  $to = 'jkanatzar@tdsclinical.com,apritchard@tdsclinical.com';
  $subject = 'ReconRx Webinar Registration';

  $msg = "<style>table, td, th { border: 1px solid black; border-collapse: collapse; padding: 3px;}</style>
          <p>Pharmacy Registration Completed for:</p>

            <table border: >
              <tr>
                <th>Pharmacy Name</th>
                <th>NCPDP</th>
                <th>Software</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Time</th>
              </tr>
              <tr>
                <td>$in{'pharmacy_name'}</td>
                <td>$in{'ncpdp'}</td>
                <td>$in{'software'}</td>
                <td>$in{'fname'}</td>
                <td>$in{'lname'}</td>
                <td>$in{'email'}</td>
                <td>$in{'phone'}</td>
                <td>$in{'time_sel'}</td>
              </tr>
             </table>";

=cut
            Pharmacy Name: $in{'pharmacy_name'}<br>
            NCPDP: $in{'ncpdp'}<br>
            Software: $in{'software'}<br>
            First Name: $in{'fname'}<br>
            Last Name: $in{'lname'}<br>
            Email: $in{'email'}<br>
            Phone: $in{'phone'}<br>
            Time: $in{'time_sel'}<br><br>
=cut


  &send_email($from, $to, $subject, $msg)
}

#______________________________________________________________________________
#______________________________________________________________________________

