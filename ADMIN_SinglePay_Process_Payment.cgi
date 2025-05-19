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

my $user = 'SinglePayAdmin';
$user = $LOGIN if($LOGIN);
$user    =~ s/\@pharmassess.com//;

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

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;
print "<hr />";

#______________________________________________________________________________

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&readPharmacies;

### POST DATA IN
$inTransfer = $in{'Transfer'};
$inDeposit  = $in{'Deposit'};
$inCheck    = $in{'Check'};
$inAmount   = $in{'Amount'};
$inSP_NCPDP = $in{'SP_NCPDP'};
$inSP_GROUP = $in{'SP_GROUP'};
$Assignment = $in{'Assignment'};
$Condition  = $in{'Condition'};
%used_chks = ();

&build_check_hash();

if ($Assignment =~ /yes/i && $inSP_NCPDP >= 0) {
  &getSinglePayCustomers;
  &updateSinglePayData;
} elsif ($inCheck !~ /^\s*$/ && $inAmount !~ /^\s*$/) {
  &getSinglePayCustomers;
  print qq#<form action="$PROG" method="post">#;
  &showSinglePayData;
  &showRemitData;
  &paymentAssign;
  print qq#</form>#;
} else {
  print "<p>No data has been passed into this program.</p>";
}

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub showSinglePayData {
  my $DBNAME = "reconrxdb";
  my $TABLE  = "singlepay";

  my $sql = "SELECT Status, TransferDate, DepositDate, PaymentType, CheckInfo, Amount, PharmacyName, NCPDPSelected, SPGroup, Check_ID
               FROM $DBNAME.$TABLE sp
              WHERE CheckInfo = '$inCheck' 
                 && Amount = $inAmount";
  
  print qq#<p>Bank Data:</p>#;
  print qq#<table class="borders">#;
  print qq#
  <tr>
  <th>Transfer</th>
  <th>Deposited</th>
  <th>Type</th>
  <th>Check Info</th>
  <th>Amount</th>
  </tr>
  \n#;

  my $sthp  = $dbx->prepare("$sql");
  $sthp->execute;
  while ( my @row = $sthp->fetchrow_array() ) {
    ($Status, $TransferDate, $DepositDate, $PaymentType, $CheckInfo, $Amount, $PharmacyName, $NCPDPSelected, $SPGroup, $Check_ID) = @row;
	
    print qq#
	<tr>
	<td>$TransferDate</td>
	<td>$DepositDate</td>
	<td>$PaymentType</td>
	<td>$CheckInfo ($PharmacyName)</td>
	<td class="money">$Amount</td>
	</tr>
	\n#;	
  }
  print qq#</table>#;
  $sthp->finish;
}

#______________________________________________________________________________

sub showRemitData {
  ### Let's try to find the store based on the check amount and single pay status
  $found_ncpdp = '';
  $found_name  = '';
  $found_check  = '';
  $found_amount  = '';
  $DepositDate =~ s/-//g;
  my $sql = '';
  
  #First, search production remits.
  $sql = "SELECT a.Check_ID, a.Pharmacy_ID, a.R_TS3_NCPDP, b.Pharmacy_Name, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date, a.R_TPP, a.R_PENDRECV, a.R_CheckReceived_Date, Check_ID
               FROM ReconRxDB.Checks a
          LEFT JOIN officedb.pharmacy b
                 ON a.Pharmacy_ID = b.Pharmacy_ID
              WHERE a.R_BPR02_Check_Amount = $inAmount 
                AND b.Single_Pay = 'Yes' ";

  if ($Condition =~ /Assign/i ) {
#    $sql .= "AND ( a.R_PENDRECV = 'P' || ( a.R_PENDRECV = 'R' AND a.R_BPR16_Date = '$DepositDate') )";
    $sql .= "AND ( a.R_PENDRECV = 'P' || ( a.R_PENDRECV = 'R' AND a.R_CheckReceived_Date >= DATE(CURRENT_TIMESTAMP - INTERVAL 14 Day) ) )";
#    $sql .= "AND a.R_PENDRECV = 'P'";
  } elsif ($Condition =~ /Review/i ) {
#    $sql .= "AND ( a.R_PENDRECV = 'P' || ( a.R_PENDRECV = 'R' AND (a.R_CheckReceived_Date IS NULL || a.R_CheckReceived_Date='') ) )";
    $sql .= "AND ( a.R_PENDRECV = 'P' || ( a.R_PENDRECV = 'R' AND a.R_CheckReceived_Date = DATE(CURRENT_TIMESTAMP) ) )";
  }

  $sql .= " ORDER BY a.R_JAddedDate DESC";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
#  print "$sqlout";

  $sthfp  = $dbx->prepare($sql);
  $sthfp->execute;
  $numofrows_prod = $sthfp->rows;
  
  print qq#<div class="archive padding">\n#;
  if ($numofrows_prod > 0) {
    print qq#<p>Potential Remit Data Match(es):</p>#;
    print qq#<table class="borders">#;
    print qq#
    <tr>
    <th>NCPDP</th>
    <th>Pharmacy</th>
    <th>Check\#</th>
    <th>Amount</th>
    <th>Date</th>
    <th>TPP</th>
    <th>Status</th>
    <th>Received Date</th>
    <th>Confirm</th>
    </tr>
    \n#;

    while ( my ($found_Check_ID, $found_Pharmacy_ID, $found_ncpdp, $found_name, $found_check, $found_amount, $found_date, $found_tpp, $found_pendrecv, $found_recdate) = $sthfp->fetchrow_array() ) {
      if ($Condition =~ /Assign/i ) {
        next if ( $used_chks{$found_Check_ID} );
      } elsif ($Condition =~ /Review/i ) {
        next if ( $used_chks{$found_Check_ID} && $found_Check_ID != $Check_ID );
      }

      if ($found_Check_ID == $Check_ID) {
        $selected = 'checked';
      } else {
        $selected = '';
      }

      $found_pendrecv_select = qq#
      <input align="center" type="checkbox" name="UPDATEREMIT\#\#$found_Pharmacy_ID\#\#$found_check\#\#$found_amount\#\#$found_Check_ID" value="$found_pendrecv" $selected></input> &nbsp; 
      #;
	  
      print qq#
      <tr>
      <td>$found_ncpdp</td>
      <td>$found_name</td>
      <td>$found_check</td>
      <td>$found_amount</td>
      <td>$found_date</td>
      <td>$found_tpp</td>
      <td>$found_pendrecv</td>
      <td>$found_recdate</td>
      <td style="text-align: center">$found_pendrecv_select</td>
      </tr>
      \n#;
    }
    print qq#</table>#;
  } else {
    print qq#<p class="yellow"><strong>No Potential Matches Found in Production Remit Data.</strong></p>#;
  }
  print qq#</div>\n#;
  $sthfp->finish;
}


#______________________________________________________________________________

sub getSinglePayCustomers {
  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";
  
  %SP_NCPDPs = ();
  %SP_NAMEs  = ();
  %SP_GROUPs  = ();

  ### Get Pharmacies List
  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name 
               FROM $DBNAME.$TABLE
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                AND Single_Pay = 'Yes'";
  my $sthsp  = $dbx->prepare("$sql");
  $sthsp->execute;
  my $numofrows = $sthsp->rows;

  if ($numofrows > 0) {
    while ( my ($Pharmacy_ID, $ncpdp, $name) = $sthsp->fetchrow_array() ) {
      my $key = "$ncpdp##$name";
      $SP_NCPDPs{$Pharmacy_ID} = $ncpdp;
      $SP_NAMEs{$Pharmacy_ID}  = $name;	  
    }
  }
  $sthsp->finish;
  
  ### Get Groups List
  my $TABLE  = "pharmacy_groups";
  my $sql = "SELECT PGGroup, PGEmail, PGNCPDPs, PGPharmacy_IDs
               FROM $DBNAME.$TABLE
              WHERE PGType = 'SinglePay'";
  my $sthsp  = $dbx->prepare("$sql");
  $sthsp->execute;
  my $numofrows = $sthsp->rows;

  if ($numofrows > 0) {
    while ( my ($group, $emails, $ncpdps, $Pharmacy_IDs) = $sthsp->fetchrow_array() ) {
      my $key = $group;
#      $SP_GROUPs{$key} = $ncpdps;  
      $SP_GROUPs{$key} = $Pharmacy_IDs;  
    }
  }
  $sthsp->finish;
}

#______________________________________________________________________________

sub paymentAssign {
  #The reason this is not in another sub is because of 'pre-selecting' the best guess pharmacy
  my $options_pharmacies = '';
  $options_pharmacies .= "<option value='0'>No Pharmacy</option>\n";
  foreach my $key (sort{$SP_NAMEs{$a} cmp $SP_NAMEs{$b}} keys %SP_NAMEs) {
    my $print_ncpdp = $SP_NCPDPs{$key};
    my $print_name  = $SP_NAMEs{$key};
#    (my $key2       = $key) =~ s/##/ - /g;
    my $selected = '';
    if ($key == $found_ncpdp) { $selected = 'selected'; } else { $selected = ''; }

    $options_pharmacies .= "<option value='$key' $selected>$print_ncpdp - $print_name</option>\n";
  }
  
  #The reason this is not in another sub is because of 'pre-selecting' the best guess group
  my $options_groups = '';
  $options_groups .= "<option value=''>No Group</option>\n";

  foreach my $key (sort keys %SP_GROUPs) {
    my $group_stores = $SP_GROUPs{$key};
    my $selected = '';
    if ($group_stores =~ /$found_ncpdp/i) { $selected = 'selected'; } else { $selected = ''; }
    $options_groups .= "<option value='$key' $selected>$key</option>\n";
  }
  
  #print qq#<form action="$PROG" method="post">#;
  
  print qq#<table>\n#;
  print qq#<tr><td class="no_border" style="padding-right: 40px;">\n#;
  print qq#<p>Assign to Pharmacy:</p>\n#;
  print qq#<p><select name="SP_NCPDP" style="width: 300px;">\n#;
  print $options_pharmacies;
  print qq#</select></p>\n#;
  print qq#</td><td class="no_border">\n#;
  print qq#<p>Assign to Group:</p>\n#;
  print qq#<p><select name="SP_GROUP" style="width: 200px;">\n#;
  print $options_groups;
  print qq#</select></p>\n#;
  print qq#</td></tr>\n#;
  print qq#</table>#;
  
  print qq#<hr />\n#;
  
  print qq#
  <INPUT name='Transfer'   TYPE="hidden" VALUE="$TransferDate">
  <INPUT name='Deposit'    TYPE="hidden" VALUE="$DepositDate">
  <INPUT name='Check'      TYPE="hidden" VALUE="$CheckInfo">
  <INPUT name='Amount'     TYPE="hidden" VALUE="$Amount">
  <INPUT name='Assignment' TYPE="hidden" VALUE="yes">
  #;
  print qq#<p><INPUT class="button-form" TYPE="submit" VALUE="Assign Bank Data to Pharmacy"></p>\n#;
  
  #print qq#</form>\n#;
  
  print qq#<a href="ADMIN_SinglePay_Assign_Payments.cgi">or go back...</a>\n#;
}

#______________________________________________________________________________

sub updateSinglePayData {
  my $DBNAME = "reconrxdb";
  my $TABLE  = "singlepay";
  my $mark_check_id = 0;

  my $useStatus = "";
  if ( $inSP_GROUP =~ /^\s*$/ ) {
     $useStatus = "Pending";
  } else {
     $useStatus = "Review";
  }

  if ( $inSP_NCPDP =~ /^\s*$/ || $inSP_NCPDP == 0) {
    $NCPDP = 0;
  } else {
    $NCPDP = $Pharmacy_NCPDPs{$inSP_NCPDP};
  }

  #Mark remit as pend/recv
  #name="UPDATEREMIT\#\#$found_ncpdp\#\#$found_check\#\#$found_amount"
  my $marked_as_recv = '';

  foreach my $key (sort keys %in) {
    next if ( $key !~ /UPDATEREMIT/i );
    my @pcs = split('##', $key);
    my $mark_Pharmacy_ID = $pcs[1];
    my $mark_ncpdp  = $SP_NCPDPs{$mark_Pharmacy_ID};
    my $mark_check  = $pcs[2];
    my $mark_amount = $pcs[3];
    $mark_check_id  = $pcs[4];
    my $value = $in{$key};

    print "Check_ID: $mark_check_id<br>";

    #Set remit to 'R' for received
    my $TABLE  = "835remitstb";
#    $Check_ID = $mark_check_id if ( $value =~ /R/i );

    if ( $value =~ /P/i ) {
      my $nsql = "UPDATE $DBNAME.checks
                     SET R_PENDRECV = 'R',
                         R_CheckReceived_Date = now(),
                         R_PostedBy = 'ReconRx',
                         R_PostedByUser = '$user',
                         R_PostedByDate = now()
                   WHERE Check_ID = $mark_check_id";
      my $sthsur2  = $dbx->prepare($nsql);
      $sthsur2->execute;
      my $numofrows = $sthsur2->rows;

      if ($numofrows > 0) {
        $marked_as_recv .= "<p>Remit for <strong>Check# $mark_check</strong> marked as '$value' for <strong>NCPDP $mark_ncpdp</strong></p>";
      }

      $sthsur2->finish;
    }
  }
  
  #Set SinglePay line status
  my $sql = "UPDATE $DBNAME.$TABLE 
                SET Status = '$useStatus', 
                    NCPDPSelected = $NCPDP,
                    Pharmacy_IDSelected = $inSP_NCPDP,
                    SPGroup = '$inSP_GROUP',
                    Check_ID = $mark_check_id
              WHERE CheckInfo = '$inCheck' 
                 && Amount = $inAmount
                 && TransferDate = '$inTransfer'
                 && DepositDate  = '$inDeposit'";

  my $sthsu  = $dbx->prepare("$sql");
  $sthsu->execute;
  my $numofrows = $sthsu->rows;

  if ($numofrows > 0) {
    #Find pharmacy name
    my $pharmacy_name = 'No Pharmacy';
    foreach my $key (sort keys %SP_NAMEs) {
      if ($key =~ /$inSP_NCPDP/gi && $inSP_NCPDP > 0) {
        $pharmacy_name = $SP_NAMEs{$key};
      }
    }
	
    my $useSP_Group = "";
    if ( $inSP_GROUP =~ /^\s*$/ ) {
       $useSP_Group = "No Group";
    } else {
       $useSP_Group = $inSP_GROUP;
    }

    #Print Output
    print "
    <p>You have assigned single pay entry:</p>
	<table>
    <tr><td>Bank Check:   </td><td>$inCheck</td></tr>
	<tr><td>Bank Amount:  </td><td>$inAmount</td></tr>
    <tr><td>Set Pharmacy: </td><td><strong>$pharmacy_name</strong> ($inSP_NCPDP)</td></tr>
	<tr><td>Set Group:    </td><td><strong>$useSP_Group</strong></td></tr>
	</table>
	$marked_as_recv<br />
	";
  }

#  $sthsu->finish;
  
  print qq#<p><a href="ADMIN_SinglePay_Assign_Payments.cgi">Assign Pending Payments</a></p>#;
  
  print qq#<p><a href="ADMIN_SinglePay_Review.cgi">Review Assigned Payments</a></p>#;
}

#______________________________________________________________________________

sub build_check_hash {
  my $DBNAME = "reconrxdb";
  my $TABLE  = "singlepay";

  my $sql = "SELECT Check_ID
               FROM $DBNAME.$TABLE sp
              WHERE Status = 'Sent'
                AND Check_ID IS NOT NULL";
  
  my $sthp  = $dbx->prepare("$sql");
  $sthp->execute;
  while ( my @row = $sthp->fetchrow_array() ) {
    my ($Check_ID) = @row;
    $used_chks{$Check_ID}++;
  }
  print qq#</table>#;
  $sthp->finish;
}

#______________________________________________________________________________
#______________________________________________________________________________
