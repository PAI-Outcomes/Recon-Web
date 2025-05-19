#______________________________________________________________________________
#
# Jay Herder
# Date: 04/12/2013
# ADMIN_All_TPP_Aging.cgi
# Mods: 05/23/2017. jlh
#______________________________________________________________________________

use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$uberdebug++;
if ($uberdebug) {
# $incdebug++;
  $debug++;
  $verbose++;
}
#####$dbitrace++;
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

$debug++ if ( $verbose );

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$VALID      = $in{'VALID'};
$isAdmin    = $in{'isAdmin'};
$LTYPE      = $in{'LTYPE'};
$LDATEADDED = $in{'LDATEADDED'};
$RUSER      = $in{'RUSER'};
$RPASS      = $in{'RPASS'};

($USER)     = &StripJunk($USER);
($PASS)     = &StripJunk($PASS);
($RUSER)    = &StripJunk($RUSER);
($RPASS)    = &StripJunk($RPASS);

$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";

#______________________________________________________________________________
&readLogins;
#($isMember, $VALID) = &isReconRxMember($USER, $PASS);

&readsetCookies;

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

# if ADMIN:

# print "USER : $USER, RUSER: $RUSER<br>\n";
# print "inNCPDP: $inNCPDP<br>\n";
# print "PASS: $PASS, RPASS, $RPASS<br>\n";

#______________________________________________________________________________

print "\nProg: $prog &nbsp; &nbsp; \nDate: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);
print "cookie_server: $cookie_server<br>\n" if ($debug);

if ( $debug ) {
  print "<br>isAdmin: $isAdmin<br>\n";
  print "dol0: $0<br>\n";
  print "prog: $prog, dir: $dir, ext: $ext<br>\n" if ($verbose);
  print "<hr size=4 noshade color=blue>\n";
  print "PROG: $PROG<br>\n";
  print "<br>\n";
  print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
  my $key;
  foreach $key (sort keys %in) {
     next if ( $key =~ /PASS/i );
     print "key: $key, val: $in{$key}<br>\n";
  }
  print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
  print "<hr size=4 noshade color=blue>\n";
}

($PROG = $prog) =~ s/_/ /g;
print qq#<strong>$PROG</strong>\n#;

#______________________________________________________________________________

$dbin    = "TCDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

print "\n\ndbin: $dbin, DBNAME: $DBNAME, TABLE: $TABLE<br>\n" if ($debug);

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&displayPage;

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
  
  print "The prog is '$prog' and the directory is '$dir'.<br>\n" if ( $debug );
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
 
sub displayPage {

  print "sub displayPage: Entry.<br>\n" if ($debug);

  $dbg = DBI->connect("DBI:mysql:$PHDBNAME:$DBHOST",$dbuser,$dbpwd,
		 { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
		
		
  $Total   = 0;
  $F1to44  = 0;
  $F45to59 = 0;
  $F60to89 = 0;
  $Fover90 = 0;
  
  $Overall_Total   = 0;
  $Overall_F1to44  = 0;
  $Overall_F45to59 = 0;
  $Overall_F60to89 = 0;
  $Overall_Fover90 = 0;
  
  $sql = qq#
SELECT LPAD(overall.dbBinParent,6,0) BIN, Third_Party_Payer_Name, 
total, IFNULL(1to44,0) 1to44, IFNULL(45to59,0) 45to59, IFNULL(60to89,0) 60to89, IFNULL(over90,0) over90,
dbProcessorControlNumber, dbGroupID
FROM (
	SELECT dbBinParentdbkey, dbBinParent, sum(dbTotalAmountPaid) total, dbProcessorControlNumber, dbGroupID
	FROM reconrxdb.incomingtb 
	WHERE dbBinParentdbkey != -1
	GROUP BY dbBinParentdbkey
) overall

LEFT JOIN officedb.third_party_payers 
ON dbBinParentdbkey = Third_Party_Payer_ID

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid) 1to44 FROM reconrxdb.incomingtb 
WHERE 
dbBinParentdbkey != -1 && 
(DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 44 DAY) && DATE(dbDateTransmitted) <= CURDATE())
GROUP BY dbBinParentdbkey
) set_1to44
ON set_1to44.dbBinParentdbkey = overall.dbBinParentdbkey 

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid) 45to59 FROM reconrxdb.incomingtb 
WHERE 
dbBinParentdbkey != -1 && 
(DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 59 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY))
GROUP BY dbBinParentdbkey
) set_45to59
ON set_45to59.dbBinParentdbkey = overall.dbBinParentdbkey

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid) 60to89 FROM reconrxdb.incomingtb 
WHERE 
dbBinParentdbkey != -1 && 
(DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 89 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 60 DAY))
GROUP BY dbBinParentdbkey
) set_60to89
ON set_60to89.dbBinParentdbkey = overall.dbBinParentdbkey

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid) over90 FROM reconrxdb.incomingtb 
WHERE 
dbBinParentdbkey != -1 && 
(DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
GROUP BY dbBinParentdbkey
) set_over90 
ON set_over90.dbBinParentdbkey = overall.dbBinParentdbkey 

\#ORDER BY Third_Party_Payer_Name ASC 
ORDER BY overall.total DESC 
  #;

  print "<pre>sql:<br>$sql<br></pre><br>\n" if ($debug);

  $sthg = $dbg->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;

  print "<table>";
  print "
  <tr>
  <th>BIN</th>
  <th>Payer</th>
  <th class=\"align_right\">Total</th>
  <th class=\"align_right\">1 to 44</th>
  <th class=\"align_right\">45 to 59</th>
  <th class=\"align_right\">60 to 89</th>
  <th class=\"align_right\">Over 90</th>
  </tr>
  ";
  while (my @row = $sthg->fetchrow_array()) {
	my ($BIN, $TPP, $Total, $F1to44, $F45to59, $F60to89, $Fover90, $dbProcessorControlNumber, $dbGroupID) = @row;
	
	$Overall_Total   += $Total;
	$Overall_F1to44  += $F1to44;
	$Overall_F45to59 += $F45to59;
	$Overall_F60to89 += $F60to89;
	$Overall_Fover90 += $Fover90;
	
	$Total   = &commify(sprintf("%0.0f", $Total));
	$F1to44  = &commify(sprintf("%0.0f", $F1to44));
	$F45to59 = &commify(sprintf("%0.0f", $F45to59));
	$F60to89 = &commify(sprintf("%0.0f", $F60to89));
	$Fover90 = &commify(sprintf("%0.0f", $Fover90));
	
	print "
	<tr>
	<td>$BIN</td>
	<td>$TPP</td>
	<td class=\"money\" style=\"background: #DDD;\">\$$Total</td>
	<td class=\"money\">\$$F1to44</td>
	<td class=\"money\">\$$F45to59</td>
	<td class=\"money\">\$$F60to89</td>
	<td class=\"money\">\$$Fover90</td>
	</tr>
	";
	
	#print qq#($All_Aging, $F1to44, $F45to59, $F60to89, $Fover90)\n# if ($debug);
  }
  
	# print "
	# <tr>
	# <td>&nbsp;</td>
	# <td>Overall Totals</td>
	# <td class=\"money\" style=\"background: #DDD;\">\$<strong>$Overall_Total</strong></td>
	# <td class=\"money\">\$<strong>$Overall_F1to44</strong></td>
	# <td class=\"money\">\$<strong>$Overall_F45to59</strong></td>
	# <td class=\"money\">\$<strong>$Overall_F60to89</strong></td>
	# <td class=\"money\">\$<strong>$Overall_Fover90</strong></td>
	# </tr>
	# ";
  
  print "</table>";
  
  $sthg->finish();
  $dbg->disconnect;
  
  print "sub displayPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________
#______________________________________________________________________________
