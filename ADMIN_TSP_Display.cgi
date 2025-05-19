#______________________________________________________________________________
#
# Jay Herder
# Date: 08/15/2012
##
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
#####print "dol0: $0\nprog: $prog, dir: $dir, ext: $ext\n";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp\;";

#$uberdebug++;
if ( $uberdebug ) {
#  $incdebug++;
   $debug++;
   $verbose++;
}
#####$dbitrace++;

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;


$debug   = $in{'debug'}   if (!$debug);
$verbose = $in{'verbose'} if (!$verbose);

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$VALID      = $in{'VALID'};
$isAdmin    = $in{'isAdmin'};
$CUSTOMERID = $in{'CUSTOMERID'};
$isMember   = $in{'isMember'};
$RUSER      = $in{'RUSER'};
$RPASS      = $in{'RPASS'};

($CUSTOMERID) = &StripJunk($CUSTOMERID);
($USER)       = &StripJunk($USER);
($PASS)       = &StripJunk($PASS);
 
$SORT    = $in{'SORT'};

$inNPI   = $dispNPI   if ( $dispNPI && !$inNPI );
$inNCPDP = $dispNCPDP if ( $dispNCPDP && !$inNCPDP );

$dispNPI   = $inNPI   if ( $inNPI && !$dispNPI );
$dispNCPDP = $inNCPDP if ( $inNCPDP && !$dispNCPDP );

$debug++ if ( $verbose );
$dbin     = "RIDBNAME";
$db       = $dbin;
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBTPNDS{"$dbin"};
$FIELDS2  = $DBTPNDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

my $HASH   = $HASHNAMES{$dbin};

#______________________________________________________________________________

&readsetCookies;

if ( $USER ) {
   $inNCPDP   = $USER;
   $dispNCPDP = $USER;
} else {
   $inNCPDP   = $in{'inNCPDP'};
   $dispNCPDP = $in{'dispNCPDP'};
}
if ( $PASS ) {
   $inNPI   = $PASS;
   $dispNPI = $PASS;
} else {
   $inNPI   = $in{'inNPI'};
   $dispNPI = $in{'dispNPI'};
}

#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);

# print qq#USER: $USER, PASS: $PASS, VALID: $VALID, isMember: $isMember\n# if ($debug);

if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;

} else {

#  &ReconRxHeaderBlock("No Side Nav");
#  &ReconRxMembersLogin;
   &ReconRxGotoNewLogin;

   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);


if ( $debug ) {
  print "RUSER: $RUSER, RPASS: $RPASS<br>\n";
  print "Cookie_RUSER: $Cookie_RUSER, Cookie_RUSER: $Cookie_RUSER<br>\n";
  print "dbin: $dbin, db: $db, DBNAME: $DBNAME, TABLE: $TABLE<br>\n";
  print "inNCPDP: $inNCPDP, inNPI: $inNPI, RUSER: $RUSER<br>\n";
  print "FIELDS : $FIELDS, FIELDS2: $FIELDS2, fieldcnt: $fieldcnt<br>\n";

# print "<hr size=4 noshade color=blue>\n";
# print "JJJ:<br>\n";
  my $key;
  foreach $key (sort keys %in) {
     next if ( $key =~ /^PASS\s*$/ );	# skip printing out the password...
#    print "key: $key, val: $in{$key}<br>\n" if ($debug);
  }
  print "<hr size=4 noshade color=blue>\n";
}
#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

print "\nProg: $prog &nbsp; &nbsp;<br>Date: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
#______________________________________________________________________________

my @fieldnames = ();

print "dbin: $dbin<br>DBNAME: $DBNAME<br>TABLE: $TABLE<hr>\n" if ($debug);

# if ( $debug ) {
#  print "FIELDS: $FIELDS ($$FIELDS)\n";
#  print "FIELDS2 array - $FIELDS2\n";
#  foreach $field (@$FIELDS2) {
#     print "FIELDS2: $field\n";
#  }
#  print "-"x72, "\n";
# }

# connect to the incomingdb MySQL database

$dbx = DBI->connect("DBI:mysql:$RIDBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

print "-"x72, "\n" if ($verbose);
@pcs = split(", ", $$FIELDS);
foreach $pc (@pcs) {
  $key = "RI##$pc";
  $pchead = $HEADINGS{"$key"} || $pc;
# print "pc: '$pc', pchead: $pchead\n" if ($debug);
  push(@fieldnames, "$pchead");
}

#______________________________________________________________________________

$FirstName = $LFirstNames{$USER};
$LastName  = $LLastNames{$USER};

if ( $RUSER ) {
   $Pharmacy_Name = $Pharmacy_Names{$RUSER};
} else {
   $Pharmacy_Name = $Pharmacy_Names{$inNCPDP};
}
# $ntitle = "<i>Contact Us</i> Assistance for $Pharmacy_Name";
$ntitle = "<i>ReconRx ADMIN menu</i>";

# Name found already in isMember subroutine
print qq#<h3>$ntitle - $LFirstName $LLastName ( $USER )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;
     
# Close the Database
$dbx->disconnect;


exit(0);

#______________________________________________________________________________

sub displayAdminPage {

  print qq#<!-- displayAdminPage -->\n#;
  print "sub displayAdminPage: Entry.<br>\n" if ($debug);


  print "<HR><HR>TELL JAY and JOSH TO FINISH THIS PAGE!!!!!<hr><hr>\n";

  @dbins = ("RIDBNAME", "RADBNAME");
  foreach $dbin (@dbins) {
    $DBNAME   = $DBNAMES{"$dbin"};
    $TABLE    = $DBTABN{"$dbin"};

    $sql = "SELECT * FROM $DBNAME.$TABLE where dbTCode IN ('TSP', 'PDF TSP') ";

    print "sql: $sql<P>\n";

    $sth99 = $dbx->prepare($sql);
    $sth99->execute();

    my $NumOfRows = $sth99->rows;

    if ( $NumOfRows > 0 ) {
       print "$dbin Rows Found: $NumOfRows<br>\n";
       while ( my @row = $sth99->fetchrow_array() ) {
          print "$dbin - row: ", join(" ## ", @row), "<hr>\n";
          #($LType, $LFirstName, $LLastName, $CUSTOMERID) = @row;
       }
    } else {
       print "No Rows Found in $dbin<br>\n";
    }
  
    $sth99->finish;
  }

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________
