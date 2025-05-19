use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $nopayments = 1;
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

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

#______________________________________________________________________________

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};
my $sp_notes;

print "\n\ndbin: $dbin, DBNAME: $DBNAME, TABLE: $TABLE<br>\n" if ($debug);

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);


$inSP_GROUP = $in{'SP_GROUP'};
$inSP_TRANSFER_DATE = $in{'SP_TRANSFER_DATE'};

&getSinglePayCustomers;
if ( $in{'displayReview'} =~ /yes/i && $inSP_GROUP !~ //i) { 
  &displayReview;
} else {
  &displaySelection;
}

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub displaySelection {
  #The reason this is not in another sub is because of 'pre-selecting' the best guess group
  my $options_groups = '';
  $options_groups .= "<option value=''>No Group</option>\n";
  foreach my $key (sort keys %SP_GROUPs) {
    my $group_stores = $SP_GROUPs{$key};
    $options_groups .= "<option value='$key'>$key</option>\n";
  }
  
  my $DBNAME = "reconrxdb";
  my $TABLE  = "singlepay";
  my $options_transfer_dates = '';
  my $sql = "SELECT TransferDate 
               FROM $DBNAME.$TABLE  
              WHERE Status = 'Review' 
           GROUP BY TransferDate 
           ORDER BY TransferDate";
  my $sthsp  = $dbx->prepare("$sql");
  $sthsp->execute;
  my $numofrows = $sthsp->rows;
  if ($numofrows > 0) {
    while ( my @row = $sthsp->fetchrow_array() ) {
      my ($date) = @row;
      $options_transfer_dates .= "<option value='$date'>$date</option>\n";
    }
  } else {
    $options_transfer_dates .= "<option value=''>No Dates Found</option>\n";
  }
  $sthsp->finish;
  
  print qq#<form action="$PROG" method="post">\n#;
  
  print qq#<p>Select Group:</p>#;
  print qq#<p><select name="SP_GROUP" style="width: 200px;">\n#;
  print $options_groups;
  print qq#</select></p>\n#;
  
  print qq#<p>Select Transfer Date:</p>#;
  print qq#<p><select name="SP_TRANSFER_DATE" style="width: 200px;">\n#;
  print $options_transfer_dates;
  print qq#</select></p>\n#;
  
  print qq#<INPUT name='displayReview' TYPE="hidden" VALUE="yes">\n#;
  
  print qq#<p><INPUT class="button-form" TYPE="submit" VALUE="Display Review"></p>\n#;
  
  print qq#</form>\n\n#;
}

#______________________________________________________________________________


sub displayReview {
  my $DBNAME = "reconrxdb";
  my $TABLE  = "singlepay";
  my $TABLE2 = "singlepay_notes";
  
  %SPR_DepositDates = ();
  %SPR_PaymentTypes = ();
  %SPR_CheckInfos   = ();
  %SPR_Amounts      = ();
  %SPR_NCPDPs       = ();
  %SPR_GROUPs       = ();
  
  %unique_stores    = ();

  my $sql = "SELECT DepositDate, PaymentType, CheckInfo, Amount, Pharmacy_IDSelected, SPGroup, notes  
               FROM $DBNAME.$TABLE  a
               LEFT JOIN $DBNAME.$TABLE2 b ON a.SPGroup = b.sp_group && a.transferdate = b.trans_date
              WHERE Status = 'Review' 
                 && TransferDate = '$inSP_TRANSFER_DATE' 
                 && SPGROUP = '$inSP_GROUP'
           ORDER BY Pharmacy_IDSelected DESC, DepositDate, PaymentType";
  my $sthp  = $dbx->prepare("$sql");
  $sthp->execute;
  my $numofrows = $sthp->rows;
  if ($numofrows > 0) {
    while ( my @row = $sthp->fetchrow_array() ) {
      my ($DepositDate, $PaymentType, $CheckInfo, $Amount, $Pharmacy_IDSelected, $SPGroup, $notes) = @row;
	  
      my $key = "$Pharmacy_IDSelected##$DepositDate##$CheckInfo##$Amount";
      $nopayments = 1;
      $sp_notes               = $notes;
      $SPR_DepositDates{$key} = $DepositDate;
      $SPR_PaymentTypes{$key} = $PaymentType;
      $SPR_CheckInfos{$key}   = $CheckInfo;
      $SPR_Amounts{$key}      = $Amount;
#      $SPR_NCPDPs{$key}       = $NCPDPSelected;
      $SPR_Pharmacy_IDs{$key} = $Pharmacy_IDSelected;
      $SPR_GROUPs{$key}       = $SPGroup;

      $unique_stores{$Pharmacy_IDSelected} = $Pharmacy_IDSelected;
    }
  } else {
    $nopayments = 0;
    print "<p>No payments found</p>\n";
  }
  $sp_notes  =~ s/<br \/>/\n/g;
  $sthp->finish;
  
  print "<p><strong>Subject</strong>: ReconRx SinglePay: $inSP_TRANSFER_DATE Money Transfer Summary</p>";
  
  print "<p><strong>Group</strong>: $inSP_GROUP</p>";
  
  print "<hr />\n";
  #print "<h2>SinglePay</h2>";
  
  print "<table width=100%>\n";
  
  my $group_total = 0;
  
  my $pharmacy_name = 'No Pharmacy';
  foreach my $key (sort keys %unique_stores) {
    #Loop FOREACH unique store, skip 0 for now.
    next if ($key == 0);

    my $Pharmacy_ID = $key;
    my $pharmacy_name = $SP_NAMEs{$Pharmacy_ID};
    my $ncpdp = $SP_NCPDPs{$Pharmacy_ID};
    print qq#<tr><td colspan=5 class="no_border"><p><strong>$pharmacy_name</strong> ($ncpdp)</p></td></tr>\n#;
	
    print qq#
    <tr>
    <th>Deposit Date</th>
    <th>Type</th>
    <th>Check Details</th>
    <th class="align_right">Amount</th>
    <th>&nbsp;</th>
    </tr>
    #;
	
    my $ncpdp_subtotal = 0;
    foreach my $key (sort keys %SPR_Pharmacy_IDs) {
      #Loop FOREACH check per ncpdp
      if ($key =~ /^$Pharmacy_ID/i) {
        $ncpdp_subtotal += $SPR_Amounts{$key};
        my $amount_display = commify(sprintf("%.2f", $SPR_Amounts{$key}));
        print qq#
        <tr>
        <td>$SPR_DepositDates{$key}</td>
        <td>$SPR_PaymentTypes{$key}</td>
        <td>$SPR_CheckInfos{$key}</td>
        <td class="align_right">\$$amount_display</td>
        <td class="align_center">  
        <form action="ADMIN_SinglePay_Process_Payment.cgi" method="post">
          <INPUT name='Check'  TYPE="hidden" VALUE="$SPR_CheckInfos{$key}">
	  <INPUT name='Amount' TYPE="hidden" VALUE="$SPR_Amounts{$key}">
	  <INPUT name='Condition' TYPE="hidden" VALUE="Review">
	  <INPUT class="button-form" TYPE="submit" VALUE="Edit">
	</form>
	</td>
        </tr>
        #;
      }
    }

    $group_total += $ncpdp_subtotal;
    $ncpdp_subtotal = commify(sprintf("%.2f", $ncpdp_subtotal));
    print qq#<tr><td colspan=3>&nbsp;</td><td class="align_right"><strong>\$$ncpdp_subtotal</strong></td></td><td>&nbsp;</td></tr>\n#;
  }
  
  foreach my $key (sort keys %unique_stores) {
    next if ($key != 0);
	print "<tr><th colspan=5>&nbsp;</th></tr>\n";
	foreach my $key (sort keys %SPR_Pharmacy_IDs) {
	  if ($key =~ /^0##/i) {
	    $group_total += $SPR_Amounts{$key};
	    my $amount_display = commify(sprintf("%.2f", $SPR_Amounts{$key}));
	    print qq#
		<tr>
		<td colspan=2 class="no_border">&nbsp;</td>
		<td class="no_border">$SPR_CheckInfos{$key}</td>
		<td class="align_right  no_border"><strong>$amount_display</strong></td>
		<td class="align_center no_border">
		  <form action="ADMIN_SinglePay_Process_Payment.cgi" method="post">
		  <INPUT name='Check'  TYPE="hidden" VALUE="$SPR_CheckInfos{$key}">
		  <INPUT name='Amount' TYPE="hidden" VALUE="$SPR_Amounts{$key}">
		  <INPUT class="button-form" TYPE="submit" VALUE="Edit">
		  </form>
                </td>
		</tr>
		\n#;
	  }
    }
  }
  
  $group_total = commify(sprintf("%.2f", $group_total));
  print "<tr><th colspan=5>&nbsp;</th></tr>\n";
  print qq#
  <tr>
  <td colspan=2 class="no_border">&nbsp;</td>
  <td class="no_border"><strong>Total Money Transfer</strong><br />$inSP_TRANSFER_DATE</td>
  <td class="align_right no_border"><strong>\$$group_total</strong></td>
  <td class="no_border">&nbsp;</td>
  </tr>
  \n#;
  
  print "</table>\n";
  print "<table>\n";
  print qq#
    <th>NOTES:</th>
    <tr>
      <td>
        <textarea name='Notes' id='Notes'  rows="4" cols="157" TYPE="text" >$sp_notes</textarea>
      </td>
      <td>
      </td>
    \n#;

  if ($nopayments) {
    print qq#
      <td>
        <INPUT class="button-form" TYPE="submit" VALUE="Save" onclick='saveNotes()'; >
      </td>
      <td>
        <img src="/images/loader_small.gif" id='gif' />
      </td>
    \n#;
  }

  print qq#
      <td>
        <INPUT id='Group' TYPE="hidden" VALUE="$inSP_GROUP">
        <INPUT id='TDate' TYPE="hidden" VALUE="$inSP_TRANSFER_DATE">
      </td>
      </tr>
    <script>
      document.getElementById('gif').style.visibility = 'hidden';
      function saveNotes() {
        document.getElementById('gif').style.visibility = 'visible';
        notes =  document.getElementById("Notes").value;
        group =  document.getElementById("Group").value;
        tdate =  document.getElementById("TDate").value;
        notes = notes.replace(/(\\n)+/g, '<br />'); 
        notes = notes.replace(/\\t/g, ' '); 

        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange=function() {
        if (this.readyState == 4 && this.status == 200) {
          document.getElementById('gif').style.visibility = 'hidden';
          alert(this.responseText);
        }
      };
      var url ="includes/savenotes.pl?Notes=" +notes + "&Group=" + group + "&TDate=" + tdate ;
         xhttp.open("POST", url, true);
           xhttp.send();
      }

    </script>
  \n#;
  print "<table>\n";
  
  print qq#<hr /><p><a href="ADMIN_SinglePay_Review.cgi">Back to Review Selection</a></p>#;
}

#______________________________________________________________________________


sub getSinglePayCustomers {
  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";
  
  %SP_NCPDPs = ();
  %SP_NAMEs  = ();
  %SP_GROUPs  = ();

  ### Get Pharmacies List
  my $sql = "
  SELECT Pharmacy_ID, NCPDP, Pharmacy_Name 
  FROM $DBNAME.$TABLE
  WHERE 
  Single_Pay = 'Yes' 
  ";
  my $sthsp  = $dbx->prepare("$sql");
  $sthsp->execute;
  my $numofrows = $sthsp->rows;
  if ($numofrows > 0) {
    while ( my @row = $sthsp->fetchrow_array() ) {
      my ($Pharmacy_ID, $ncpdp, $name) = @row;
	  my $key = "$Pharmacy_ID";
	  $SP_NCPDPs{$key} = $ncpdp;
	  $SP_NAMEs{$key}  = $name;	  
    }
  }
  $sthsp->finish;
  
  ### Get Groups List
  my $TABLE  = "pharmacy_groups";
  my $sql = "
  SELECT PGGroup, PGEmail, PGNCPDPs, PGPharmacy_IDs 
  FROM $DBNAME.$TABLE
  WHERE 
  PGType = 'SinglePay' 
  ";
  my $sthsp  = $dbx->prepare("$sql");
  $sthsp->execute;
  my $numofrows = $sthsp->rows;
  if ($numofrows > 0) {
    while ( my @row = $sthsp->fetchrow_array() ) {
      my ($group, $emails, $ncpdps, $Pharmacy_IDs) = @row;
	  my $key = $group;
#	  $SP_GROUPs{$key} = $ncpdps;  
	  $SP_GROUPs{$key} = $Pharmacy_IDs;  
    }
  }
  $sthsp->finish;
}

#______________________________________________________________________________
#______________________________________________________________________________
