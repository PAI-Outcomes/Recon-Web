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
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$setup_tpp      = $in{'setup_tpp'};
$setup_pharmacy = $in{'setup_pharmacy'};

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

&hasAccess($USER);

if ( $ReconRx_Admin_835_Not_Set_Up !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
#  print qq#<a href="Login.cgi">Log In</a><P>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#Get additional data
&readThirdPartyPayers;

#Start page operations

&displayOptions;
  
if ($setup_tpp !~ /^\s*$/) {
  &processTPPData;
}

if ($setup_pharmacy !~ /^\s*$/) {
  &processPharmacyData;
}

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub displayOptions {
  print "<hr>\n";
  
  print qq#<form action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<p>Select a Third Party Payer</p>#;
  print qq#<select name="setup_tpp" class="recon-dropdown-form" onchange="this.form.submit()">\n#;
  print qq#<option value="">Select a Payer</option>\n#;
  
  my $DBNAME = "officedb";
  my $TABLE  = "third_party_payers";

  my $sql = "SELECT Third_Party_Payer_ID, BIN, Third_Party_Payer_Name  
               FROM $DBNAME.$TABLE 
              WHERE Status = 'Active' 
                 && Primary_Secondary = 'Pri' 
                 && Reconcile = 'Yes' 
                 && BIN NOT LIKE '99999%' 
           ORDER BY Third_Party_Payer_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my @row = $sthx->fetchrow_array() ) {
    my ($TPP_ID, $TPP_BIN, $TPP_NAME) = @row;
    print qq#<option value="$TPP_ID\#\#$TPP_NAME">$TPP_ID - $TPP_NAME</option>\n#;
  }
  $sthx->finish;
  print qq#</select>#;
  print qq#</form>#;
  

  print qq#<form action="$PROG" method="post" style="display: inline-block;">#;
  print qq#<p>or Select a Pharmacy</p>#;
  print qq#<select name="setup_pharmacy" class="recon-dropdown-form" onchange="this.form.submit()">\n#;
  print qq#<option value="">Select a Pharmacy</option>\n#;
  
  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name, CentralPay835
               FROM officedb.pharmacy 
              WHERE Status_ReconRx = 'Active'
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name, CentralPay835
               FROM officedb.pharmacy_coo
              WHERE Status_ReconRx = 'Active'
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($Pharmacy_ID, $NCPDP, $Pharmacy_Name, $CentralPay835) = $sthx->fetchrow_array() ) {
    $Pharmacy_Names{$Pharmacy_ID}  = $Pharmacy_Name;
    $Pharmacy_NCPDPs{$Pharmacy_ID} = $NCPDP;
    print qq#<option value="$Pharmacy_ID\#\#$NCPDP\#\#$Pharmacy_Name\#\#$CentralPay835">$NCPDP - $Pharmacy_Name</option>\n#;
  }

  $sthx->finish;
  print qq#</select>#;
  print qq#</form>#;
  
  print qq#<br /><br /><hr />\n#;
}

#______________________________________________________________________________

sub processPharmacyData {
  my ($Pharmacy_ID, $NCPDP, $Pharmacy_Name, $CentralPay835) = split('##', $setup_pharmacy);
  
  print qq#<div><h2 style="display: inline;">$Pharmacy_Name ($NCPDP)</h2><span class="right">Central Pay 835: $CentralPay835<span></div><br style="clear: both;" />\n#;
  
  my %agingBins;
  my %remitBins;
  my %problemBins;
  
  my $DBNAME = "reconrxdb";

  ### Gather REMIT information ### ------------------------------------------------------
  my $sql = "SELECT R_TPP_PRI, R_TPP, max(R_BPR16_Date) as Latest_Remit, DATEDIFF(max(R_BPR16_Date), CURDATE()) as Date_Diff
               FROM $DBNAME.Checks
              WHERE pharmacy_id = $Pharmacy_ID
           GROUP BY R_TPP_PRI";
  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($R_TPP_PRI, $R_TPP, $Latest_Remit, $Date_Diff) = $sthr->fetchrow_array() ) {
    $remitBins{$R_TPP_PRI} = $R_TPP_PRI;
    if ($Date_Diff <= -30) {
      $problemBins{$R_TPP_PRI} = "No check dates since $Latest_Remit";
    }
  }
  $sthr->finish;
  
  ### Gather SWITCH information ### -----------------------------------------------------
  my $sql = "SELECT dbBinParentdbkey, dbBinNumber, dbDateTransmitted 
               FROM $DBNAME.incomingtb 
              WHERE pharmacy_id = $Pharmacy_ID
                 && dbDateTransmitted != ''
           GROUP BY dbBinParentdbkey";

  my $sthi  = $dbx->prepare("$sql");
  $sthi->execute;

  while ( my ($dbBinParentdbkey, $dbBinNumber, $dbDateTransmitted) = $sthi->fetchrow_array() ) {
    $agingBins{$dbBinParentdbkey} = $dbBinParentdbkey;
    if (!$remitBins{$dbBinParentdbkey}) {
      $problemBins{$dbBinParentdbkey} = "No remit data";
    }
  }
  $sthi->finish;
  
  ### Apply Exceptions ### --------------------------------------------------------------
  my $exceptionApplied = 0;
  
  my $sql = "SELECT IF_TPP_ID_IS_SET_UP, THEN_TPP_ID_IS_ALSO_SET_UP 
               FROM $DBNAME.835_not_set_up_exceptions";

  my $sthe  = $dbx->prepare("$sql");
  $sthe->execute;

  while ( my ($IF_TPP_ID_IS_SET_UP, $THEN_TPP_ID_IS_ALSO_SET_UP) = $sthe->fetchrow_array() ) {
    #Look through all remit parent IDs and apply exceptions
    foreach $key (sort keys %remitBins) {
      if ($key == $IF_TPP_ID_IS_SET_UP && $problemBins{$THEN_TPP_ID_IS_ALSO_SET_UP}) {
        #IF an exception ID is present AND its associated ID is a problem BIN, remove it (it's not really a problem)
        delete $problemBins{$THEN_TPP_ID_IS_ALSO_SET_UP};
        $exceptionApplied++;
      }
    }
  }
  $sthe->finish;
  
  ### Display Results ### ---------------------------------------------------------------
  if (keys %problemBins > 0) {
    print qq#<table style="width:100%;">\n#;
    print qq#<tr><th>TPP</th><th>ID</th><th>Problem</th></tr>\n#;
  
    foreach $key (sort {$TPP_Names{$a} cmp $TPP_Names{$b}} keys %problemBins) {
      print qq#<tr><td>$TPP_Names{$key}</td><td>$key</td><td>$problemBins{$key}</td></tr>\n#;
    }
  
    print qq#</table>\n#;
  
    if ($exceptionApplied > 0) {
      print qq#<p class="align_right">* using $exceptionApplied exception filters</p>\n#;
    }
  
  } else {
    #No problems in problem hash
    print qq#<p>No problems found!</p>\n#;
  }
  
}

#______________________________________________________________________________

sub processTPPData {
  my ($TPP_ID, $TPP_NAME) = split('##', $setup_tpp);
  print qq#<h2>$TPP_NAME ($TPP_ID)</h2>\n#;
  
  my %agingPharmacies;
  my %remitPharmacies;
  my %problemPharmacies;
  
  my $DBNAME = "reconrxdb";
  
  ### Gather REMIT information ### ------------------------------------------------------
  my $sql = "SELECT R_TPP_PRI, R_TPP, pharmacy_id, max(R_BPR16_Date) as Latest_Remit, DATEDIFF(max(R_BPR16_Date), CURDATE()) as Date_Diff
               FROM $DBNAME.Checks
              WHERE R_TPP_PRI=$TPP_ID
                AND R_TS3_NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
           GROUP BY pharmacy_id";

  my $sthr  = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($R_TPP_PRI, $R_TPP, $Pharmacy_ID, $Latest_Remit, $Date_Diff) = $sthr->fetchrow_array() ) {
#    $R_TS3_NCPDP = sprintf("%07d", $R_TS3_NCPDP);
#    $remitPharmacies{$R_TS3_NCPDP} = $R_TS3_NCPDP;
    $remitPharmacies{$Pharmacy_ID} = $Pharmacy_ID;
    if ($Date_Diff <= -30) {
      $problemPharmacies{$Pharmacy_ID} = "No check dates since $Latest_Remit";
    }
  }
  $sthr->finish;
  
  ### Gather SWITCH information ### -----------------------------------------------------
  my $sql = "SELECT b.Pharmacy_Name, overall.Pharmacy_ID
               FROM (SELECT Pharmacy_ID, sum(dbTotalAmountPaid) total
                       FROM $DBNAME.incomingtb 
                      WHERE dbBinNumber = $TPP_BINs{$TPP_ID}
                   GROUP BY Pharmacy_ID
                    ) overall
          LEFT JOIN ( SELECT Pharmacy_ID, Pharmacy_Name, Status_ReconRx
                        FROM officedb.pharmacy
                   UNION ALL
                      SELECT Pharmacy_ID, CONCAT(Pharmacy_Name, ' (COO)'), Status_ReconRx
                        FROM officedb.pharmacy_coo
                    ) b
                 ON overall.Pharmacy_ID = b.Pharmacy_ID
              WHERE b.Status_ReconRx = 'Active'
           ORDER BY b.Pharmacy_Name ASC";

  my $sthi  = $dbx->prepare("$sql");
  $sthi->execute;

  while ( my ($Pharmacy_Name, $Pharmacy_ID) = $sthi->fetchrow_array() ) {
#    $NCPDP = sprintf("%07d", $NCPDP);
#    $agingPharmacies{$NCPDP} = $NCPDP;
    $agingPharmacies{$Pharmacy_ID} = $Pharmacy_ID;
    if (!$remitPharmacies{$Pharmacy_ID}) {
      $problemPharmacies{$Pharmacy_ID} = "No remit data";
    }
  }
  $sthi->finish;
  
  ### Apply Exceptions ### --------------------------------------------------------------
  my $exceptionApplied = 0;
  
  #Use selected TPP ID to find any associated exceptions that might affect it.
  my $sql = "SELECT IF_TPP_ID_IS_SET_UP 
               FROM $DBNAME.835_not_set_up_exceptions
              WHERE THEN_TPP_ID_IS_ALSO_SET_UP = $TPP_ID";
  my $sthe  = $dbx->prepare("$sql");
  $sthe->execute;

  while ( my ($ASSOCIATED_EXCEPTION_TPP_ID) = $sthe->fetchrow_array() ) {
    #Loop through each pharmacy we've identified as a problem
    #Query that pharmacy's remits to see if the exception found above applies
    foreach my $Pharmacy_ID (sort keys %problemPharmacies) {
      my $sql = "SELECT R_TPP_PRI
                   FROM $DBNAME.Checks
                  WHERE R_TPP_PRI = $ASSOCIATED_EXCEPTION_TPP_ID 
                    AND Pharmacy_Id = $Pharmacy_ID
                  LIMIT 1";

      my $sthl  = $dbx->prepare("$sql");
      $sthl->execute;

      while ( my @row = $sthl->fetchrow_array() ) {
        my ($R_TPP_PRI) = @row;
        #If the pharmacy has received remits from the exception payer, remove from the problems hash
        if ($R_TPP_PRI) {
          delete $problemPharmacies{$Pharmacy_ID};
          $exceptionApplied++;
        }
      }
      $sthl->finish;
    }
  }
  $sthe->finish;
  
  ### Display Results ### ---------------------------------------------------------------
  if (keys %problemPharmacies > 0) {
    print qq#<table style="width:100%;">\n#;
    print qq#<tr><th>Pharmacy</th><th>NCPDP</th><th>Problem</th></tr>\n#;
  
    foreach $key (sort {$Pharmacy_Names{$a} cmp $Pharmacy_Names{$b}} keys %problemPharmacies) {
      next if (!$Pharmacy_Names{$key}); #If name is not set, pharmacy did not meet selection box criteria above.
#      $key = sprintf("%07d", $key);
      print qq#<tr><td>$Pharmacy_Names{$key}</td><td>$Pharmacy_NCPDPs{$key}</td><td>$problemPharmacies{$key}</td></tr>\n#;
    }
  
    print qq#</table>\n#;
  
    if ($exceptionApplied > 0) {
      print qq#<p class="align_right">* using $exceptionApplied exception filters</p>\n#;
    }
  
  } else {
    #No problems in problem hash
    print qq#<p>No problems found!</p>\n#;
  }
}  

#______________________________________________________________________________
