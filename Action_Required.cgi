
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$tdate  = sprintf("%04d%02d%02d", $year, $month, $day);
$DATEEX = sprintf("%02d/%02d/%04d", $month, $day, $year);
#______________________________________________________________________________

&readPharmacies(0, $PROGRAM, $inNCPDP);

if ( $USER ) {
  if($Pharmacy_Arete{$PH_ID} =~ /B|E/) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
   ##&MyAreteRxHeader;
   ##&AreteRxHeaderBlock;
  }
  else {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
  }
} 
else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

print << "EOL";
<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
<script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
<style>
div#alert-nav { 
	font-size: 16px;
	position: relative;
	float:left;
	background: #f2f2f2;
	width:400px;
	margin: 0px;
	padding: 0px;
	text-align:center;
}

div#alert-nav ul { 
	list-style-type:none;
	margin: 0px; 
	padding:0; 
}
	
div#alert-nav ul li{ 
	position: relative;
	display: block;
	padding: 0px; 
	margin: 2px 0px; 
	text-align: center;
        border: 2px solid #133562;
}

div#alert-nav ul li a { 
	color:#133562;
	display: block;
	margin: 0 0 0 0;
	padding: 8px 0px;
	text-decoration: none;
}

div#alert-nav ul li a.highlight { 
	color:#ffffff;
	text-decoration:none;
	font-weight:bold;
}
	
div#alert-nav ul li a:hover { 
	color:#ffffff;
	background-color: #5FC8ED;
	text-decoration:none;	
	}
</style>
EOL

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

$ntitle = "Action(s) Required";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

print qq#<h2>Please complete the following action(s):</h2>\n#;

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;
  print qq#  <div id="alert-nav">\n#;
  print qq#    <ul>\n#;

  $sql = "SELECT action, url
            FROM officedb.pharmacy_action_req
           WHERE Pharmacy_ID = $PH_ID
             AND program = '$PROGRAM'
        ORDER BY date_added";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;

  $sth = $dbx->prepare($sql);
  $sth->execute();

  while ( my ( $action, $url ) = $sth->fetchrow_array()) {
    print qq#   <li><a href="$url">$action</a></li>\n#;
  }

  $sth->finish;
  print qq#    </ul>\n#;
  print qq#    </div>\n#;
}

#______________________________________________________________________________
