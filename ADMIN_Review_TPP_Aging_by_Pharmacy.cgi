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

$select_bin     = $in{'select_bin'};
$select_status  = $in{'select_status'};
$select_problem = $in{'select_problem'};

$save_select_bin = $select_bin;

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

($title = $prog) =~ s/_/ /g;
print qq#<strong>$title</strong>\n#;

#______________________________________________________________________________

$dbin    = "TCDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&displayPage;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#-------------------------------------- 
#
&local_doend($print_run_time);
print "<hr>\n";
#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

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
  $dbin    = "RIDBNAME";
  $DBNAME  = $DBNAMES{"$dbin"};
  $TABLE   = $DBTABN{"$dbin"};

  ($filterPCN) = &getFilterPayers($in_TPP_ID,$in_TPP_BIN,$in_TPP_NAME);

  print "<hr>\n";
  
  print qq#<form action="$PROG" method="post">#;
  print qq#<p>Select a payer to see the aging breakdown by pharmacy</p>#;
  print qq#<select name="select_bin" class="recon-dropdown-form">\n#;
  print qq#<option value="">Select a Payer</option>\n#;
 
  foreach $key (sort { $filter_PayerNames{$a} cmp $filter_PayerNames{$b} } keys %filter_PayerNames) {
    my $TPP_ID   = $filter_PayerIDs{$key};
    my $TPP_BIN  = $filter_PayerBINs{$key};
    my $TPP_NAME = $filter_PayerNames{$key};

#   print qq#<option value="$TPP_BIN">$TPP_BIN - $TPP_NAME</option>\n#;
    my $value = "${TPP_ID}##${TPP_BIN}##${TPP_NAME}";
    print qq#<option value="$value">$TPP_ID - $TPP_BIN - $TPP_NAME</option>\n#;

    $JBINNAMES{$TPP_BIN} = $TPP_NAME;
  }
  print qq#</select>#;
   
  print qq#&nbsp; <INPUT class="button-form" TYPE="submit" VALUE="Select Payer">#;
  print qq#</form>#; 

  return if ( $save_select_bin =~ /^\s*$/ );
  #----------------------------------------------------------------------------------------

  ($TPP_ID, $TPP_BIN, $TPP_NAME) = split("##", $save_select_bin, 3);
# print qq#<p><strong>Now viewing payer $save_select_bin - $JBINNAMES{$save_select_bin}</strong></p>\n#;
  print qq#<p><strong>Now viewing payer: TPP_ID: $TPP_ID  //  BIN: $TPP_BIN  //  NAME: $TPP_NAME</strong></p>\n#;
  
  #------------------------------

  $Total   = 0;
  $F1to44  = 0;
  $F45to59 = 0;
  $F60to89 = 0;
  $Fover90 = 0;

  $sql = "SELECT Pharmacy_Name, overall.dbNCPDPNumber as NCPDP, IFNULL(1to44,0) 1to44, IFNULL(45to59,0) 45to59, IFNULL(60to89,0) 60to89, IFNULL(over90,0) over90 
            FROM ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid) total
                     FROM $DBNAME.incomingtb 
                    WHERE dbBinParentdbkey = $TPP_ID
                       && dbBinParent      = $TPP_BIN
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) overall
       LEFT JOIN ( SELECT Pharmacy_ID, Pharmacy_Name, Status_ReconRx
                     FROM officedb.pharmacy
                    UNION
                   SELECT Pharmacy_ID, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name, Status_ReconRx
                     FROM officedb.pharmacy_coo
                 ) all_pharm
              ON overall.Pharmacy_ID = all_pharm.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid) 1to44
                     FROM $DBNAME.incomingtb 
                    WHERE dbBinParentdbkey = $TPP_ID
                       && dbBinParent      = $TPP_BIN
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 44 DAY) && DATE(dbDateTransmitted) <= CURDATE())
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_1to44
              ON set_1to44.Pharmacy_ID = overall.Pharmacy_ID 
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid) 45to59
                     FROM $DBNAME.incomingtb 
                    WHERE dbBinParentdbkey = $TPP_ID
                       && dbBinParent      = $TPP_BIN
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 59 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY))
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_45to59
              ON set_45to59.Pharmacy_ID = overall.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid) 60to89
                     FROM $DBNAME.incomingtb 
                    WHERE dbBinParentdbkey = $TPP_ID
                       && dbBinParent      = $TPP_BIN
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 89 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 60 DAY))
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_60to89
              ON set_60to89.Pharmacy_ID = overall.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid) over90 FROM $DBNAME.incomingtb 
                    WHERE dbBinParentdbkey = $TPP_ID
                       && dbBinParent      = $TPP_BIN
                       && (DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_over90 
              ON set_over90.Pharmacy_ID = overall.Pharmacy_ID 
           WHERE Status_ReconRx = 'Active'
        ORDER BY Pharmacy_Name ASC";

  $sthg = $dbx->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;

  print "<table>";
  print "
  <tr>
  <th>NCPDP</th>
  <th>Pharmacy</th>
  <th class=\"align_right\">1 to 44</th>
  <th class=\"align_right\">45 to 59</th>
  <th class=\"align_right\">60 to 89</th>
  <th class=\"align_right\">Over 90</th>
  </tr>
  ";
  while (my @row = $sthg->fetchrow_array()) {
    my ($pharmname, $ncpdp, $F1to44, $F45to59, $F60to89, $Fover90) = @row;
    $All_Aging   = &commify(sprintf("%0.2f", $All_Aging));
    $F1to44  = &commify(sprintf("%0.2f", $F1to44));
    $F45to59 = &commify(sprintf("%0.2f", $F45to59));
    $F60to89 = &commify(sprintf("%0.2f", $F60to89));
    $Fover90 = &commify(sprintf("%0.2f", $Fover90));
    
    print "
    <tr>
    <td>$ncpdp</td>
    <td>$pharmname</td>
    <td class=\"money\">\$$F1to44</td>
    <td class=\"money\">\$$F45to59</td>
    <td class=\"money\">\$$F60to89</td>
    <td class=\"money\">\$$Fover90</td>
    </tr>
    ";
    
    #print qq#($All_Aging, $F1to44, $F45to59, $F60to89, $Fover90)\n# if ($debug);
  }
  print "</table>";
  
  $sthg->finish();
}

#______________________________________________________________________________
#______________________________________________________________________________
