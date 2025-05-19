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

	<img id="image_top" src="../images/Shiny_blue_wave_background5.png" alt="TDS Clinical" title="">

EOF

#______________________________________________________________________________

$DBNAME     = 'ReconRxDB';
$TABLE      = 'register';
$tbl_gerimed= 'gerimed_membership';

$dbx = DBI->connect("DBI:mysql:$DBNAME:$dbhost",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);
my $validate = 0;

$INCPDP = sprintf("%07d", $in{'ncpdp'});


my %NCPDP;

&get_ncpdps;

if ($NCPDP{$INCPDP}) {
  $return = &add_registry();
  $validate = 1;
}
else {
  &email_ram();
}

&display_webpage($return);
print "</div>\n</body>\n</html>";

$dbx->disconnect;

exit(0);

#______________________________________________________________________________
sub get_ncpdps {
  $sql = "SELECT NCPDP 
            FROM $DBNAME.$tbl_gerimed
         ";
  my $sth = $dbx->prepare("$sql");
  $sth->execute();

  while (($NCPDP) = $sth->fetchrow_array() ) {
    $NCPDP{$NCPDP}++; 
  }
}

sub add_registry {
  my $retval = 1;
  my $fname =  "$in{'name'}";
  my $ncpdp =  "$in{'ncpdp'}";

  my $sth = $dbx->prepare("INSERT INTO $DBNAME.$TABLE (fname, ncpdp)
             VALUES (?,?)");

#  print "SQL: $sql<br>";
$sth->execute("$fname", "$ncpdp");
  return($retval);
}

#______________________________________________________________________________

sub display_webpage {

 if($validate) {
    $training = 'https://www.youtube.com/embed/LZ_E7L2kQmE';
   print <<EOL;
   <div class='signup_body'>
     <img id="signup_img" src="../images/ReconRX_LogoWTag_SM.jpg" alt="ReconRx" title="">
      <iframe width="800" height="600" src="$training?rel=0" frameborder="0" allowfullscreen></iframe>
   </div>
EOL
 }
 else {
   print <<EOL;
   <div class='signup_body'>
     <img id="signup_img" src="../images/ReconRX_LogoWTag_SM.jpg" alt="ReconRx" title="">
     <p style='text-align: center; font-size: 18px; color: #063970; font-weight: bold;'>$in{'time_sel'}</p>
     <p style='text-align: center;'>Again, thank you for your interest in the ReconRx Reconciliation Demo.  A customer representative will contact you shortly with a link to the demo.</p>
   </div>
EOL
 }
}

#______________________________________________________________________________

sub email_ram {
  my $from = "NoReply";

##  $to = 'sdowning@tdsclinical.com';
  $to = 'RECON@tdsclinical.com,sdowning@tdsclinical.com';
  $subject = 'ReconRx Demo Link Request';

  $msg = "<style>table, td, th { border: 1px solid black; border-collapse: collapse; padding: 3px;}</style>
          <p>Pharmacy Demo Link Request For:</p>

            <table border: >
              <tr>
                <th>NCPDP</th>
                <th>Name</th>
                <th>Email</th>
              </tr>
              <tr>
                <td>$INCPDP</td>
                <td>$in{'name'}</td>
                <td>$in{'email'}</td>
              </tr>
             </table>";


  &send_email($from, $to, $subject, $msg)
}

#______________________________________________________________________________
#______________________________________________________________________________

