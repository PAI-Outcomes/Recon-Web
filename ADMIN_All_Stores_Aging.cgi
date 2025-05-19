use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________
&readLogins;

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

&displayPage;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

print "<hr>\n";
#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub displayPage {
  $dbg = DBI->connect("DBI:mysql:$PHDBNAME:$DBHOST",$dbuser,$dbpwd,
		 { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
		
  $Total   = 0;
  $F1to44  = 0;
  $F45to59 = 0;
  $F60to89 = 0;
  $Fover90 = 0;

  $sql = "SELECT Pharmacy_Name, overall.Pharmacy_ID as Pharmacy_ID, overall.dbNCPDPNumber as NCPDP,
                 IFNULL(1to44,0) 1to44, IFNULL(45to59,0) 45to59, IFNULL(60to89,0) 60to89, IFNULL(over90,0) over90 
            FROM ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) total
                     FROM reconrxdb.incomingtb 
                    WHERE dbBinParentdbkey != -1
                       && dbBinParentdbkey NOT IN ( SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                      FROM officedb.third_party_payers
                                                     WHERE Reconcile = 'NO'
                                                  )
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) overall
       LEFT JOIN ( SELECT Pharmacy_ID, Pharmacy_Name, Type, Status_ReconRx, Status_ReconRx_Clinic, Term_Date_ReconRx, Term_Date_ReconRx_Clinic
                     FROM officedb.pharmacy
                    UNION
                   SELECT Pharmacy_ID, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name, Type, Status_ReconRx, Status_ReconRx_Clinic, Term_Date_ReconRx, Term_Date_ReconRx_Clinic
                     FROM officedb.pharmacy_coo
                 ) all_pharm
              ON overall.Pharmacy_ID = all_pharm.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) 1to44
                     FROM reconrxdb.incomingtb 
                    WHERE dbBinParentdbkey != -1
                       && dbBinParentdbkey NOT IN ( SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                      FROM officedb.third_party_payers 
                                                     WHERE Reconcile = 'NO'
                                                  )
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 44 DAY) 
                       && DATE(dbDateTransmitted) <= CURDATE())
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_1to44
              ON set_1to44.Pharmacy_ID = overall.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) 45to59
                     FROM reconrxdb.incomingtb 
                    WHERE dbBinParentdbkey != -1 
                       && dbBinParentdbkey NOT IN ( SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                      FROM officedb.third_party_payers 
                                                     WHERE Reconcile = 'NO'
                                                  )
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 59 DAY) 
                       && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY))
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_45to59
              ON set_45to59.Pharmacy_ID = overall.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) 60to89
                     FROM reconrxdb.incomingtb 
                    WHERE dbBinParentdbkey != -1 
                       && dbBinParentdbkey NOT IN ( SELECT officedb.third_party_payers.Third_Party_Payer_ID
                                                      FROM officedb.third_party_payers 
                                                     WHERE Reconcile = 'NO'
                                                  )
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 89 DAY) 
                       && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 60 DAY))
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_60to89
              ON set_60to89.Pharmacy_ID = overall.Pharmacy_ID
       LEFT JOIN ( SELECT Pharmacy_ID, dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) over90
                     FROM reconrxdb.incomingtb 
                    WHERE dbBinParentdbkey != -1
                       && dbBinParentdbkey NOT IN ( SELECT officedb.third_party_payers.Third_Party_Payer_ID
                                                      FROM officedb.third_party_payers
                                                     WHERE Reconcile = 'NO'
                                                  )
                       && (DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
                 GROUP BY Pharmacy_ID, dbNCPDPNumber
                 ) set_over90 
              ON set_over90.Pharmacy_ID = overall.Pharmacy_ID 
           WHERE Type LIKE '%ReconRx%'
              && ((Status_ReconRx='Active' || Status_ReconRx_Clinic='Active')
                  || (Status_ReconRx NOT IN ('Active', '') && (Term_Date_ReconRx IS NOT NULL && Term_Date_ReconRx > (DATE_SUB(CURDATE(), INTERVAL 8 WEEK)) ) )
                  || (Status_ReconRx_Clinic NOT IN ('Active', '') && (Term_Date_ReconRx_Clinic IS NOT NULL && Term_Date_ReconRx_Clinic > (DATE_SUB(CURDATE(), INTERVAL 8 WEEK)) ) )
                 )
        ORDER BY Pharmacy_Name ASC";

  $sthg = $dbg->prepare($sql);
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
  while ( my ($pharmname, $Pharmacy_ID, $ncpdp, $F1to44, $F45to59, $F60to89, $Fover90) = $sthg->fetchrow_array()) {
	$All_Aging = &commify(sprintf("%0.2f", $All_Aging));
	$F1to44    = &commify(sprintf("%0.2f", $F1to44));
	$F45to59   = &commify(sprintf("%0.2f", $F45to59));
	$F60to89   = &commify(sprintf("%0.2f", $F60to89));
	$Fover90   = &commify(sprintf("%0.2f", $Fover90));
	
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
  }
  print "</table>";
  
  $sthg->finish();
  $dbg->disconnect;
}

#______________________________________________________________________________
#______________________________________________________________________________
