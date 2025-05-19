
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

$UpDB_ThirdParty  = $in{'UpDB_ThirdParty'};
$UpDB_PaymentType = $in{'UpDB_PaymentType'};
$UpDB_CheckAmount = $in{'UpDB_CheckAmount'};
$UpDB_CheckNumber = $in{'UpDB_CheckNumber'};
$UpDB_CheckDate   = $in{'UpDB_CheckDate'};

($UpDB_ThirdParty)  = &StripJunk($UpDB_ThirdParty);
($UpDB_PaymentType) = &StripJunk($UpDB_PaymentType);
($UpDB_CheckAmount) = &StripJunk($UpDB_CheckAmount);
($UpDB_CheckNumber) = &StripJunk($UpDB_CheckNumber);
($UpDB_CheckDate)   = &StripJunk($UpDB_CheckDate);

$UpDB_CheckAmount =~ s/,//gi;
$UpDB_CheckAmount =~ s/$//gi;

if ( $UpDB_CheckDate =~ /\// ) {
  my @pcs = split("/", $UpDB_CheckDate, 3);
  if ( $pcs[0] > 2000 ) {
    $UpDB_CheckDate = sprintf("%04d-%02d-%02d", $pcs[0], $pcs[1], $pcs[2]);
  } else {
    $pcs[2] = $pcs[2] + 2000 if ( $pcs[2] < 100 );
    $UpDB_CheckDate = sprintf("%04d-%02d-%02d", $pcs[2], $pcs[0], $pcs[1]);
  }
} elsif ( $UpDB_CheckDate !~ /\D/ ) {
  # Only Numeric Digits
  $p1 = substr($UpDB_CheckDate, 0, 2);
  $p2 = substr($UpDB_CheckDate, 2, 2);
  $p3 = substr($UpDB_CheckDate, 4, 4);
  if ( $p3 > 2000 ) {
    $UpDB_CheckDate = sprintf("%04d-%02d-%02d", $p3, $p1, $p2);
  } else {
    $p3 = substr($UpDB_CheckDate, 0, 4);
    $p2 = substr($UpDB_CheckDate, 4, 2);
    $p1 = substr($UpDB_CheckDate, 6, 2);
    $UpDB_CheckDate = sprintf("%04d-%02d-%02d", $p3, $p2, $p1);
  }
}

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
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} 
else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

##<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
##<script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>

print << "JDO";
<script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>
<!-- <script src="/includes/validate_req.js" type="text/javascript"></script> -->
<script src="/includes/validations_for_check_entry.js"></script>

<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" />
<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script>
<script type="text/javascript" charset="utf-8">
\$(document).ready(function() {
  \$('\#tablef').dataTable( {
    "sScrollX": "100%",
    "bScrollCollapse": true, 
    "sScrollY": "350px",
    "bPaginate": false
  } );
} );
</script>

<script>
\$(function() {
\$( ".datepicker" ).datepicker();
\$( "#anim" ).change(function() {
  \$( ".datepicker" ).datepicker( "option", "showAnim", \$( this ).val() );
});
});
</script>
<script type="text/javascript">
jQuery(function(\$) {
      \$(".datepicker").mask("99/99/9999");
   });
</script>

JDO

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";

if ($PH_ID == 11 || $PH_ID == 23) {
	$RNDBNAME = "webinar";
}

#print "PH_ID: $PH_ID  RNDBNAME: $RNDBNAME\n";

&readThirdPartyPayers();
&readTPPDisplayNameOverrides();

my $FMT = "%0.02f";
@myPTs = ( "CHK", "EFT" );

my %jTPPs = ();
foreach $TPP_ID (sort { $TPP_Names{$a} cmp $TPP_Names{$b} } keys %TPP_BINs) {
  $string = "$TPP_Names{$TPP_ID}";
  next if ( $string =~ /^\s*\-\s*$/ );
  next if ( $TPP_PriSecs{$TPP_ID} !~ /^Pri$/i );
  next if ( $TPP_ID == 700006 );
  my $Parent_Name_key   = $TPP_Parent_Name_Keys{$TPP_ID};
  my $Parent_Name       = $TPP_Names{$Parent_Name_key};
  my $Parent_Reconciles = $TPP_Reconciles{$TPP_ID};

  next if ( $Parent_Reconciles =~ /^N/i );

  if ( $Parent_Name && $Parent_Name ne $string ) {
     $string = "$Parent_Name";
  }

  $jTPPs{"$string"} = $TPP_BINs{$TPP_ID};
#  print "KEY: $string - $TPP_BINs{$TPP_ID}<br>";
  $TPPName_to_TPPID{"$string"} = $TPP_ID;
  push(@myTPPs, $string);
}

@myTPPs = ();
push(@myTPPs, "-");
foreach $key (sort keys %jTPPs){
   push(@myTPPs, "$key");
}

#______________________________________________________________________________

$dbz = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&update_remitsdb;

$ntitle = "Post Check with No Remit";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

&displayWebPage;
&displayBottom;

$dbz->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;

  ($PROG = $prog) =~ s/_/ /g;

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;

  print qq#<table>\n#;
  print qq#<tr valign=top>#;
 
  $ThirdParty = "-";

  if ( $UpDB_PaymentType ) {
     $PaymentType = $UpDB_PaymentType;
  } else {
     $PaymentType = "CHK";
  }

  &dropdown( "ThirdParty" , "Third Party" , "check_tpp select-text-form", @myTPPs );
  &dropdown( "PaymentType", "Payment Type", "check_type select-text-form", @myPTs );

  print qq#<tr valign=top>#;
  print qq#<th class="">Amount $nbsp $nbsp $nbsp $nbsp\$</th>#;
  $UpDB_CheckAmount = "";	
  print qq#<th><INPUT class="check_amount input-text-form" TYPE="text" NAME="UpDB_CheckAmount" SIZE=20 MAXLENGTH=20 VALUE="$UpDB_CheckAmount"> &nbsp; </th>#;
  print qq#</tr>\n#;

  print qq#<tr valign=middle class="check_number_row">#;
  print qq#<th class="">Check \#<br></th>#;
  $UpDB_CheckNumber = "";
  print qq#<th><INPUT class="check_number input-text-form" TYPE="text" NAME="UpDB_CheckNumber" SIZE=20 MAXLENGTH=20 VALUE="$UpDB_CheckNumber"> &nbsp; </th>#;
  print qq#</tr>\n#;

  print qq#<tr valign=top>#;
  print qq#<th class="">Check Date</th>#;
  print qq#<th>\n#;
  $UpDB_CheckDate = "";
  print qq#<INPUT CLASS="datepicker check_date input-text-form" TYPE="text" NAME="UpDB_CheckDate" VALUE="$UpDB_CheckDate" SIZE=10 MAXLENGTH=10>#;
  print "$nbsp Example: $DATEEX\n";
  print qq#</th>\n#;
  print qq#</tr>\n#;

  if ($USER != 1694 ) {
    print qq#<tr><th class="align_left" colspan=2><INPUT id="submit" style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Save Changes"></th></tr>\n#;
  }
  print qq#</table>\n#;

  print qq#</FORM>\n#;
  print qq#<p class="error check_errors_text" style="display: none;">Please fix errors outlined in red above.</p>#;

}
#______________________________________________________________________________

sub dropdown {

  my ($dbvar, $label, $classString, @OPTS) = @_;

  $dbvarval = $$dbvar;
  $formname = "UpDB_" . "$dbvar";

  my $foundmatch = 0;

  print qq#  <tr>\n#;
  print qq#  <th class="" class="align_left">$label</th>\n#;
  print qq#  <th>\n#;
  print qq#    <SELECT NAME="$formname" class="$classString">\n#;
  foreach $OPT (@OPTS) {
    if ( $dbvarval =~ /^$OPT/i ) {
      $SEL = "SELECTED";
      $foundmatch++;
    } 
    else {
      $SEL = "";
    }
    print qq#      <OPTION $SEL VALUE="$OPT">$OPT</OPTION>\n#;
  }
  if ( $foundmatch <= 0 ) {
    $OPT = "--";
    print qq#      <OPTION SELECTED VALUE="$OPT">$OPT</OPTION>\n#;
  }
  print qq#    </SELECT>\n#;
  print qq#  </th></tr>\n#;
}

#______________________________________________________________________________

sub update_remitsdb {

  my $PostedBy = '';
  if ($OWNER =~ /pharmassess|tdsclinical/i) {
    $PostedBy = "ReconRx";
    $PostedByUser = $LOGIN;
  } 
  else {
    $PostedBy = "Pharmacy";
    $PostedByUser = $USER;
  }

  my $FRONT = "<FONT COLOR=RED SIZE=+1><STRONG>";
  my $BACK  = "</STRONG></FONT>";
  if ( $UpDB_ThirdParty =~ /^\s*$/ ) {
     # First time in. Blow By
  } elsif ( $UpDB_ThirdParty =~ /^-$/ ) {
     print "${FRONT}Not processing - Third Party not selected.${BACK}<br>\n";
  } elsif ( $UpDB_CheckAmount =~ /^\s*$/ ) {
     print "${FRONT}Not processing - Amount not entered.${BACK}<br>\n";
  } elsif ( $UpDB_CheckNumber =~ /^\s*$/ && $UpDB_PaymentType !~ /^EFT$/i ) {
     print "${FRONT}Not processing - Check Number not entered.</STRONG></FONT>${BACK}<br>\n";
  } elsif ( $UpDB_CheckDate =~ /^\s*$/ ) {
     print "${FRONT}Not processing - Check Date not entered.${BACK}<br>\n";
  } elsif ( $Pharmacy_Term_Date_ReconRxs{$PH_ID} ) {
      print qq#<br><br><span style="background: \#FF0;">Unfortunately, this entry cannot be saved because your pharmacy is in the ReconRx termination process. Please contact your ReconRx account manager if this information is inaccurate.</span><br><br>\n#;
      &email_ram("$Pharmacy_Names{$PH_ID} $inNCPDP attempted to complete a <i>Post Check with no Remit</i> entry for $UpDB_ThirdParty and the entry was denied. Our records indicate that the pharmacy is in the ReconRx termination process. Please verify that this information is accurate.");
  } else {

    $OCheckAmount = sprintf("$FMT", $UpDB_CheckAmount);
    $UpDB_CheckDate =~ s/\-//g;
    if ( $UpDB_PaymentType =~ /^EFT$/i ) {
       $UpDB_CheckNumber = ""; 
    }

    $jBIN = $jTPPs{"$UpDB_ThirdParty"} || $TPP_Overrides_BIN{"$UpDB_ThirdParty"};

    # Does this record already exist?
    $sql = "SELECT Check_ID
              FROM $RNDBNAME.Checks
             WHERE Pharmacy_ID = $PH_ID
               AND R_ISA_BIN = '$jBIN'
               AND R_TRN02_Check_Number = '$UpDB_CheckNumber'
               AND R_BPR02_Check_Amount = '$OCheckAmount'
               AND R_BPR16_Date = '$UpDB_CheckDate'
               AND R_PENDRECV = 'P'";

    $Prows = $dbz->do("$sql") or warn $DBI::errstr;
    #print "$sql - $Prows<br>";

    $sql = "SELECT Check_ID
              FROM $RNDBNAME.Checks
             WHERE Pharmacy_ID = $PH_ID
               AND R_ISA_BIN = '$jBIN'
               AND R_TRN02_Check_Number = '$UpDB_CheckNumber'
               AND R_BPR02_Check_Amount = '$OCheckAmount'
               AND R_BPR16_Date = '$UpDB_CheckDate'
               AND R_PENDRECV = 'R'";

    $RECrows = $dbz->do("$sql") or warn $DBI::errstr;
    #print "$sql - $RECrows<br>";

    my $TPP_ID = $TPPName_to_TPPID{"$UpDB_ThirdParty"}; 

    $sql = "SELECT 835remitstbID
              FROM reconrxdb.835remitstb 
             WHERE Pharmacy_ID = $PH_ID
               AND (R_TPP_PRI = $TPP_ID OR Payer_ID = $TPP_ID)
         UNION ALL 
            SELECT 835remitstbID
              FROM reconrxdb.835remitstb_archive 
             WHERE Pharmacy_ID = $PH_ID
               AND (R_TPP_PRI = $TPP_ID OR Payer_ID = $TPP_ID)";
    $FRDrows = $dbz->do("$sql") or warn $DBI::errstr;
    #print "$sql - $FRDrows<br>";

    if ($Prows != '0E0') {
      print qq#<span style="background: \#FF0;">The remit associated with this payment can be found in the Post Payment to Remit </span><br><br>\n#;
    }
    elsif ($RECrows != '0E0') {
      print qq#<span style="background: \#FF0;">This payment has already been reconciled in our system.<br>No record was added.</span><br><br>\n#;
    }
    elsif ($FRDrows eq '0E0' && $PH_ID != 23) {
      print qq#<br><br><span style="background: \#FF0;">Unfortunately, this entry cannot be saved. Currently, ReconRx is not receiving 835 files from $UpDB_ThirdParty for your pharmacy. Please note that your ReconRx account manager has been notified. We apologize for any inconvenience this may cause.</span><br><br>\n#;
      &email_ram("$Pharmacy_Names{$PH_ID} $inNCPDP attempted to complete a post check with no remit entry for $UpDB_ThirdParty and our records indicate that we have not received a first remit from this third party payer. Please take the appropriate action.");
    }
    else {
      $sql = "SELECT * 
                FROM $RNDBNAME.$RNTABLE
               WHERE Pharmacy_ID = $PH_ID
                 AND BIN = '$jBIN'
                 AND ThirdParty = '$UpDB_ThirdParty'
                 AND PaymentType = '$UpDB_PaymentType'
                 AND CheckNumber = '$UpDB_CheckNumber'
                 AND CheckAmount = '$OCheckAmount'
                 AND CheckDate = '$UpDB_CheckDate'";

      $SELrows = $dbz->do("$sql") or warn $DBI::errstr;

      if ( $SELrows < 1 ) {
        $sql  = "INSERT INTO $RNDBNAME.$RNTABLE 
                    SET
                        DateAdded = '$tdate',
                        NCPDP = '$inNCPDP',
                        BIN = '$jBIN',
                        ThirdParty = '$UpDB_ThirdParty',
                        PaymentType = '$UpDB_PaymentType',
                        CheckNumber = '$UpDB_CheckNumber',
                        CheckAmount = '$OCheckAmount',
                        CheckDate='$UpDB_CheckDate',
                        R_PostedBy = '$PostedBy',
                        R_PostedByUser = '$PostedByUser',
                        R_PostedByDate = NOW(),
                        Pharmacy_ID = $PH_ID ";
  
        $rows = $dbz->do("$sql") or warn $DBI::errstr;
   
        if ( !$rows ) {
          print "<strong><i>\n";
          print "<br><br>ERROR: Unable to write to the database.<br>\n";
          print "Please verify your data and try again.<br>\n";
          print "If this does not work, please contact us. Thank you.<br>\n";
          print "</i></strong>\n";
        } else {
          #RECORD TO LOGS##########
          &logActivity($LOGIN, "$Pharmacy_Name (via $PostedByUser) posted check with no remit $UpDB_CheckNumber ($UpDB_ThirdParty)", $PH_ID);
        }
      } else {
        print qq#<span style="background: \#FF0;">This Record already exists in our database.<br>No record was added.</span><br><br>\n#;
      }
    }
  }
}

#______________________________________________________________________________

sub displayBottom {

  my $TOTAL  = 0;

  print "<br>\n";
  print qq#<font size=+1><strong>Payments Added and NOT Reconciled yet</strong></font><br>\n#;
  print qq#<table id="tablef" class="main">\n#;
  print qq#<thead>\n#;
  print qq#<tr valign=top>#;
  print qq#<th>Third Party</th>\n#;
  print qq#<th>Type</th>\n#;
  print qq#<th>Check\#</th>\n#;
  print qq#<th class="align_right">Amount</th>\n#;
  print qq#<th class="align_right">Check Date</th>\n#;
  print qq#<th class="align_right">Date Added</th>\n#;
  print qq#<th class="align_right">&nbsp;</th>\n#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;

  $sql = "SELECT NCPDP, DateAdded, ThirdParty, PaymentType, CheckNumber, CheckAmount, CheckDate, R_PostedBy, Pharmacy_ID
            FROM $RNDBNAME.$RNTABLE
           WHERE Pharmacy_ID='$PH_ID'
        ORDER BY CheckDate";
   
  $sth99 = $dbz->prepare($sql) || die "Error preparing query" . $dbz->errstr;
  $sth99->execute() or die $DBI::errstr;
  my $NumOfRows = $sth99->rows;
   
  while ( my @row = $sth99->fetchrow_array() ) {
  
     my ($NCPDP, $DateAdded, $ThirdParty, $PaymentType, $CheckNumber, $CheckAmount, $CheckDate, $R_PostedBy, $Pharmacy_ID) = @row;
     my $OCheckDate = substr($CheckDate, 4, 2) . "/" . substr($CheckDate, 6, 2) . "/" . substr($CheckDate, 0, 4);
     my $ODateAdded = substr($DateAdded, 4, 2) . "/" . substr($DateAdded, 6, 2) . "/" . substr($DateAdded, 0, 4);
	 
     if ($R_PostedBy =~ /recon/i) {
       $R_PostedByTD = '<img src="/images/reconrx16px.png">';
     } else {
       $R_PostedByTD = '<div style="min-width: 16px;">&nbsp;</div>';
     }
	 
     print qq#<tr valign=top>#;
     print qq#<td>$ThirdParty</td>#;
     print qq#<td>$PaymentType</td>#;
     print qq#<td>$CheckNumber</td>#;
     my $OCheckAmount = "\$" . &commify(sprintf("$FMT", $CheckAmount));
     print qq#<td class="align_right">$OCheckAmount</td>#;
     print qq#<td class="align_right">$OCheckDate</td>#;
     print qq#<td class="align_right">$ODateAdded</td>#;
     print qq#<td class="no_border">$R_PostedByTD</td>#;
     print qq#</tr>\n#;
     $TOTAL += $CheckAmount;
  }
  
  $sth99->finish;

  my $OTOTAL = "\$" . &commify(sprintf("$FMT", $TOTAL));

  print qq#</tbody>\n#;
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>\n#;
  print qq#<P><strong>Total Payments Received Awaiting Remit: $OTOTAL<br></strong></P>#;
  
  print qq#
  <div class="notification">
    <div class="left">
	  <p>ReconRx will post your payments for you (<img src="/images/reconrx16px.png" />).<br />Please fax your check copies to:</p>
	</div>
	<div class="right">
	  <p class="left"><img src="/images/printer11.png" /> &nbsp; </p>
	  <p class="right">Toll Free Fax:<br /><strong>(888) 255-6706</strong></p>
	</div>
	<div style="clear: both;"></div>
  </div>
  \n#;
}

#______________________________________________________________________________

sub email_ram {
  my $msg = shift @_;
  my $from = "NoReply";

  &readCSRs();
  &read_emails();

  @pcs = split(/@/, $CSR_Emails{$Pharmacy_ReconRx_Account_Managers{$PH_ID}});
  $user = $pcs[0];
  $to = $EMAILACCT{$user};
  $to .= ',bprowell@tdsclinical.com';
  $subject = 'Post Check with no Remit Alert';

  &send_email($from, $to, $subject, $msg)
}
#______________________________________________________________________________
