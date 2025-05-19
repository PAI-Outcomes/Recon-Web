use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   exit(0);
}

#______________________________________________________________________________

($PROG = $prog) =~ s/_/ /g;
print qq#<strong>$PROG</strong>\n#;

#______________________________________________________________________________

$dbin    = "TCDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&displayTCodeDefs;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#-------------------------------------- 
#
# print "$prog - DONE!<br>\n" if ($verbose);
&local_doend($print_run_time);
print "<hr>\n";
#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub local_dostart {
  my ( $print_start_time ) = @_;
  print "<hr noshade size=5 color=red>\n";

  $tm_beg = time();
  ($prog, $dir, $ext) = fileparse($0, '\..*');
  #####print "dol0: $0\nprog: $prog, dir: $dir, ext: $ext<br>\n";

  my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
  $year  += 1900;	# reported as "years since 1900".
  $month += 1;	# reported ast 0-11, 0==January
  $syear  = sprintf("%4d", $year);
  $smonth = sprintf("%02d", $month);
  $sday   = sprintf("%02d", $day);
  $sdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
  $stime  = sprintf("%02d:%02d", $hour, $min);

  print qq#Started: $sdate - $stime<br>\n#;
  
  print "<hr noshade size=5 color=red>\n";
}

#______________________________________________________________________________

sub local_doend {
  my ( $print_run_time ) = @_;

  if ( $print_run_time ) {
    print "<hr noshade size=5 color=red>\n";
    my $tm_end = time();
    print "tm_end: $tm_end<br>\n" if ($incdebug);

    my $elapsed = $tm_end - $tm_beg;
#   print  "Elapsed time in seconds: ", $elapsed, "<br>\n";
#   printf ("Elapsed time in minutes: %-7.2f<br><br>\n\n", $elapsed / 60);

    my $minutes = int($elapsed / 60);
    my $seconds = $elapsed - ($minutes * 60);

    my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
    $year  += 1900;	# reported as "years since 1900".
    $month += 1;	# reported ast 0-11, 0==January
    $syear  = sprintf("%4d", $year);
    $smonth = sprintf("%02d", $month);
    $sday   = sprintf("%02d", $day);
    $sdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
    $stime  = sprintf("%02d:%02d", $hour, $min);

    print qq#Finished: $sdate - $stime<br>\n#;
    print  "$nbsp $nbsp Elapsed time in seconds: ", $elapsed, " ( $minutes minutes, $seconds seconds )<br>\n";
    print "<hr noshade size=5 color=red>\n";
  }
} 

#______________________________________________________________________________
 
sub displayTCodeDefs {
  print qq#<table>\n#;
  print qq#<TR><TH>TCode</TH><TH>Meaning</TH><TH>Association</TH></TR>\n#;
   
  my $sql = "SELECT TCode, Meaning, Association FROM $DBNAME.$TABLE ";

  print "sql:<br>$sql<br>\n" if ($incdebug);

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  my $NumOfRows = $sthx->rows;

  while ( my @row = $sthx->fetchrow_array() ) {
      print "<tr>\n";  
      print "<td>", join("</td><td>", @row), "</td>";

      print "</tr>\n";  
  }
  print qq#</table>\n#;
}

#______________________________________________________________________________
#______________________________________________________________________________
