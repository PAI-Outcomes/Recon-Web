require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use CGI;
$query = new CGI;

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";
my $PH_STRING;

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$LDATEADDED = $in{'LDATEADDED'};
$SORT       = $in{'s'};

($SORT) = &StripJunk($SORT);

print $query->redirect('https://members.recon-rx.com/cgi-bin/Post_Payment_To_Remits.html');

&readsetCookies;
&readPharmacies;
&readContacts;
&read_emails();
&readCSRs();

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock_New;
  }
  else {
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

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d-%02d-%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$todaysdate = sprintf("%04d-%02d-%02d", $year, $month, $day);

#______________________________________________________________________________
#______________________________________________________________________________

&readThirdPartyPayers;

$dbin     = "R8DBNAME";
#print "PH_ID: $PH_ID  USER: $USER\n";
if ($PH_ID == 11 || $PH_ID == 23) {
    $DBNAME = "webinar";
} elsif ($PH_ID  eq 'Aggregated' && $USER == 2612 ) {
    $DBNAME = "webinar";
} else {
    $DBNAME = $DBNAMES{"$dbin"};
}
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

my $RECPAY = 0;
my $FMT = "%0.02f";
my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );

$dbz = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&update_remitsdb;

$ntitle = "Post Payment to Remits";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage;

$dbz->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;
  print "sub displayWebPage: Entry.<br>\n" if ($debug);

  if ( $ENV =~ /dev/i ) {
    $FRONT = "HTTP://dev.Recon-Rx.com";
    $SECTYP = "http://";
  } else {
    $FRONT = "HTTPS://members.Recon-Rx.com";
    $SECTYP = "https://";
  }

  print qq#<link type="text/css" media="screen" rel="stylesheet" href="$FRONT/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="${SECTYP}cdn.datatables.net/1.10.2/js/jquery.dataTables.js"></script> \n#;
  
  ($PROG = $prog) =~ s/_/ /g;
  $URLH = "${prog}.cgi";
  
  print qq#
  <script> 
  
  \$(document).ready(function() {
  
    oTable = \$('\#tablef').dataTable( { 
	  autoWidth: false, 
      "sScrollX": "100%", 
      "bScrollCollapse": true, 
      //"sScrollY": "350px", 
      "bPaginate": false, 
	    "aaSorting": [],
	  "bLengthChange": false,
      "pageLength": 100,
      "aoColumnDefs": [
        { 'bSortable': false, 'aTargets': [ -1, -2, {"sTitle":"Confirm Payment"} ] }
      ]
    }); 
	
	chkcnt = 0;
	totamt = 0;
    \$("\#prform input[type=radio]:checked").each(function() {
	   if(this.value == "Received" && this.checked == true)
      {
        chkcnt++;
        var chkamt = \$('input[type=hidden]', \$(this).closest("td")).val();
		totamt += parseFloat(chkamt);
      }
    });	
	
	var totalamt = totamt.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
	
    \$('[id\$=amtlbl]').text("Total Payments Received: " + chkcnt + " Total Amount Received: " + totalamt);
			
			
	\$("\#submit_form").click(function(e) {
	  fnResetAllFilters(oTable);
	  \$('\#prform').submit();
	});	
	
  });  
    
  function fnResetAllFilters(oTable) {
    var oSettings = oTable.fnSettings();
    for(iCol = 0; iCol < oSettings.aoPreSearchCols.length; iCol++) {
      oSettings.aoPreSearchCols[ iCol ].sSearch = '';
    }
    oSettings.oPreviousSearch.sSearch = '';
    oTable.fnDraw();
	
	  oTable.fadeTo("fast", 0.33);

	//\$(".loading").show();	
	
  }
  
  </script> 
  \n#;
  
  $submitval = "Save Changes";
  print qq#<FORM name="prform" id="prform" ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="debug"   VALUE="$debug">\n#;
  print qq#<INPUT TYPE="hidden" NAME="verbose" VALUE="$verbose">\n#;

  print qq#<strong>Please mark all <u>Received</u> payments and click <u>$submitval</u>.</strong><br><br>\n#;
  print qq#<div class="notification emergency">IMPORTANT: If your pharmacy received a payment that is NOT listed here please <strong>ADD the check information under "<a href="Post_Check_with_No_Remit.cgi" style="color: \#FFF;">Post Check with No Remit</a>".</strong> ReconRx will automatically reconcile your payment once electronic remittance is received.</div>\n#;
  print qq#<font size=-1><i>\n#;
  print qq#All payment transaction posted may be reversed within the same business day.<br>#;
  print qq#To reverse a transaction, mark your payment as <u>PENDING</u> and click <u>$submitval</u>.\n#;
  print qq#</font></i>\n#;

  if ( $AreteUser !~ /B/i ) {
    print qq#<span style="float: right;">Please allow 15 days from the check date to receive the check.</span>\n#;
  }

  print "<hr />\n";

  print "<br>";
  
  print qq#<div style="color:red";>\n#;
  print qq#<strong>Important: Please hold off on posting November payments until December 4th</strong> so that we may capture October data for reporting purposes. <strong>Any payment marked received will not be able to be put back to a pending status </strong> once the overnight reconciliation process has ran. Please contact your ReconRx Account Manager directly if you have any questions.
  \n#;
  print "<br>";
  print qq#</div>\n#;

  if ($USER != 1694 ) {
    print qq#<br /><div style="float: right;"><button style="padding:5px; margin:0px" id="submit_form" NAME="Submit">Save Changes</button></div>\n#;
  }

  print qq#<table id="tablef" class="main">\n#;
  
  print qq#<thead>\n#;
  print qq#<tr>#;

  if ( $PH_ID  eq 'Aggregated') {
    print qq#<th>NCPDP</th>#;
  }
  print qq#<th>Third Party</th>#;
  print qq#<th>Pmt Type</th>#;
  print qq#<th class="align_center">Check /<br>ACH \#</th>#;
  print qq#<th class="align_center">Amount</th>#;
  print qq#<th class="align_center">Date</th>#;
  print qq#<th class="align_center">Confirm Payment</th>#;
  print qq#<th class="align_center">Seen</th># if ($debug);
  print qq#<th class="align_center">Check Received Date</th># if ($debug);
  print qq#<th>&nbsp;</th>#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;
  
  &display_lines;
  
  print qq#</tbody>\n#;
  
  print qq#</table>\n#;
  
  print qq#<br /><br /><div style="float: left;"><label id="amtlbl" style="color: dark blue;background-color:yellow;font-size: 18px;"></label></div>\n#;
  
  if ($USER != 1694 ) {
    print qq#<br /><br /><div style="float: right;"><button style="padding:5px; margin:5px" id="submit_form" NAME="Submit">Save Changes</button></div>\n#;
  }
  print qq#</FORM>\n#;
  
  print qq#<div style="clear: both;"></div>\n#;
  
  
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

  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________

sub display_lines {
  my $dbin     = "P8DBNAME";
  my $P8DBNAME   = $DBNAMES{"$dbin"};
  my $P8TABLE    = $DBTABN{"$dbin"};
##  if ($PH_ID  eq 'Aggregated' ) {
##      $PH_ID = $Agg_String;
##  }
  

  my $sql = qq#
    SELECT Check_ID, R_TPP, Pharmacy_ID, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, R_BPR03_CreditDebit_Flag_Code,
           R_BPR16_Date, R_TRN02_Check_Number, R_PENDRECV, R_Seen, R_CheckReceived_Date,
           R_ISA06_Interchange_Sender_ID, R_PostedBy, R_TS3_NCPDP, DATEDIFF(CURRENT_DATE, DATE(R_BPR16_Date))
      FROM $DBNAME.Checks
     WHERE (1=1)
        && Pharmacy_ID IN ($PH_STRING)
        && R_BPR02_Check_Amount != 0.00 
        && (
        (R_CheckReceived_Date IS NULL || R_CheckReceived_Date='0000-00-00' || R_CheckReceived_Date='$todaysdate')
         )
  #;

  if ( $WHICHDB =~ /Webinar/i ) {
    $sql .= qq#
      ORDER BY R_BPR16_Date DESC, R_PENDRECV DESC, R_TPP LIMIT 0,10
    #;
  } 
  else {
    $sql .= qq#
      ORDER BY R_PENDRECV DESC, R_TPP
    #;
  }
  my $sqlout = $sql;
  $sqlout =~ s/\n/<br>\n/g;
  $sqlout =~ s/ /&nbsp/g;
#  print "<hr>sql:<br>$sqlout<hr>\n" ;#if ($debug);
 
  my $stb = $dbz->prepare($sql);
  my $numofrows = $stb->execute;

  if ( $numofrows <= 0 ) {
     print "No records found for this date<br>\n";
  } else {
    while (my @row = $stb->fetchrow_array()) {
       ($Check_ID, $R_TPP, $R_Pharmacy_ID, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount, $R_BPR03_CreditDebit_Flag_Code, $R_BPR16_Date, $R_TRN02_Check_Number, $R_PENDRECV, $R_Seen, $R_CheckReceived_Date, $R_ISA06_Interchange_Sender_ID, $R_PostedBy, $NCPDP, $days_from_chk_date) = @row;

       my $Was_me = "";
       my $Use_me = "";

       $Was_me = $R_TPP;
       
       if ( $R_ISA06_Interchange_Sender_ID !~ /^\s*$/ && $R_TRN02_Check_Number !~ /^\s*$/ ) {
          ($displayNameOverride) = &findTPPDisplayNameOverride($R_ISA06_Interchange_Sender_ID, $R_TRN02_Check_Number);
          $Use_me = $displayNameOverride if ($displayNameOverride !~ /^\s*$/);
       }

       if ( $Was_me ne $Use_me ) {
       } else {
          $Use_me = $Was_me;
       }

       $Use_me = $Was_me if ( $Use_me =~ /^\s*$/ );

       $R_TRN02_Check_Number =~ s/\-/ \-<br>/g;

       my $OcheckAmount = sprintf("$FMT", $R_BPR02_Check_Amount);
       my $jdate = $R_BPR16_Date;
       my $year = substr($jdate, 0, 4);
       my $mon  = substr($jdate, 4, 2);
       my $mday = substr($jdate, 6, 2);

       if ( $R_BPR16_Date > 19000000 ) {
         $Odate = qq#$mon/$mday/$year#; 
       } else {
         $Odate = 0;
       }

       my $pendrecvname = "PENDRECV##" . $Check_ID . "##$R_BPR04_Payment_Method_Code##$R_PENDRECV";
	   my $checkamt = "CHECKAMT##" . $Check_ID . "##$R_BPR04_Payment_Method_Code##$R_PENDRECV";
       my $pendval  = "Pending";
#       $pendval  = "Missing" if ( $R_PENDRECV =~ /^M$/i && $TYPE !~ /Admin/i );
       my $misval  = "Missing";
       my $recvval  = "Received";
       if ( $R_PENDRECV =~ /^R$/i ) {
         $pendchecked = "";
         $mischecked = "";
         $recvchecked = qq#checked="checked"#;
	     $addcolor = "green";
       }
       elsif ( $R_PENDRECV =~ /^M$/i ) {
         $pendchecked = "";
         $recvchecked = "";
         $mischecked = qq#checked="checked"#;
	     $addcolor = "red";
       }
       else {
         $recvchecked = "";
         $mischecked = "";
         $pendchecked = qq#checked="checked"#;
         $addcolor    = qq##;
       }
	   
       if ($R_PostedBy =~ /recon/i) {
         $R_PostedByTD = '<img src="/images/reconrx16px.png">';
       } else {
         $R_PostedByTD = '<div style="min-width: 16px;"></div>';
       }

       print qq#<tr>#;
       if ( $PH_ID  eq 'Aggregated') {
         print qq#<td>$NCPDP</td>#;
       }
       print qq#<td class="">$Use_me</td>#;
       print qq#<td class="">$R_BPR04_Payment_Method_Code</td>#;
       print qq#<td class="align_center">$R_TRN02_Check_Number</td>#;
       print qq#<td class="align_right">$OcheckAmount</td>#;
       print qq#<td class="">$Odate</td>#;
       print qq#<td class="$addcolor" nowrap>#;
	   print qq#  <INPUT TYPE="hidden" name="$checkamt" VALUE="$R_BPR02_Check_Amount">\n#;
       print qq#  <input type="RADIO" name="$pendrecvname" value="$pendval" $pendchecked> Pending $nbsp#;
       print qq#  <input type="RADIO" name="$pendrecvname" value="$recvval" $recvchecked> Received#;
       #print qq#  <input type="RADIO" name="$pendrecvname" value="$misval" $mischecked> Missing# if ( ($TYPE =~ /Admin/i || ($AreteUser !~ /B/i && $days_from_chk_date >= 15 )) && $R_BPR02_Check_Amount > 0 );
	   print qq#  <input type="RADIO" name="$pendrecvname" value="$misval" $mischecked> Missing#;
       print qq#</td>#;
       print qq#<td class="">$R_PostedByTD</td>#;
       print qq#</tr>\n#;
    }
  }

  $stb->finish();
}

#______________________________________________________________________________

sub update_remitsdb {
  $PH_STRING = '';

  if ($PH_ID  =~ /Aggregated/i ) {
      $PH_STRING = $Agg_String;
  }
  else {
    $PH_STRING = $PH_ID;
  }

  my ($key, $val, $sql);
  my $PENDRECV = "P";
  my %savesqls = ();
  
  my $PostedBy = '';
  if ($LOGIN =~ /pharmassess|tdsclinical/i) {
    $PostedBy = "ReconRx";
	$PostedByUser = $LOGIN;
  } else {
    $PostedBy = "Pharmacy";
	$PostedByUser = $USER;
  }

  foreach $key (sort keys %in) {
     $val = $in{$key};
     #print "$key = $in{$key}<br>"; # if ($USER == 72);
     next if ( $key !~ /^PENDRECV/i);

     if      ( $val =~ /Pending/i ) {
       $PENDRECV = "P";
     } 
     elsif ( $val =~ /Received/i ) {
       $PENDRECV = "R";
     } 
     elsif ( $val =~ /Missing/i ) {
       $PENDRECV = "M";
     }
     else {
       $PENDRECV = "P";
     }
     $PENDRECV_SAVE = $PENDRECV;

     my ($PR, $Check_ID, $Payment_Method, $O_PENDRECV) = split("##", $key);

     next if ( $PENDRECV eq $O_PENDRECV );

     $sql2  = "UPDATE $DBNAME.Checks SET ";
     $sql2 .= "R_PENDRECV='$PENDRECV', ";

     if ($PENDRECV =~ /R/i) {
       $sql2 .= qq#
         R_PostedBy           = '$PostedBy',
         R_PostedByUser       = '$PostedByUser',
         R_PostedByDate       = NOW(), 
         R_CheckReceived_Date = NOW()
       #;
     }
     else {
       $sql2 .= qq#
         R_PostedBy     = NULL,
         R_PostedByUser = NULL,
         R_PostedByDate = NULL,
         R_CheckReceived_Date = NULL 
       #;
     }

     $sql2 .= qq#
       WHERE 1=1
         AND PHARMACY_ID IN ($PH_STRING)
         AND Check_ID = $Check_ID
         AND R_PENDRECV !='$PENDRECV'
     #;

     ##$sql2 .= qq#AND R_CheckReceived_Date = '$tdate'# if ( $PENDRECV =~ /P/i);

     #print "$sql2<br>";
     $sth95 = $dbz->prepare($sql2) || die "Error preparing query" . $dbz->errstr;
     $sth95->execute() or die $DBI::errstr;
     my $NumOfRows2 = $sth95->rows;
     $sth95->finish();

     if ( $PENDRECV =~ /M/i && $Payment_Method =~ /ACH/i ) {
       #print "Notify - $key = $in{$key}<br>"; # if ($USER == 72);
       my $sql = "SELECT Pharmacy_ID, R_TPP_PRI, R_TPP, R_BPR02_Check_Amount, R_BPR16_Date, R_TRN02_Check_Number
                    FROM $DBNAME.Checks
                   WHERE Check_ID = $Check_ID";

       my $stb = $dbz->prepare($sql);
       $stb->execute;

       while (my @row = $stb->fetchrow_array()) {
         ($pharmacy_id, $tpp_id, $tpp, $pmt_amt, $pmt_dte, $chk_num) = @row;
       }

       $stb->finish();

       $contact_name  = $Contacts{$pharmacy_id}{'ReconRx'}{'Payment Confirmation'}{'Name'};
       $contact_email = $Contacts{$pharmacy_id}{'ReconRx'}{'Payment Confirmation'}{'Email'};
       $acct_mgr = $Pharmacy_ReconRx_Account_Managers{$pharmacy_id};
       $ncpdp    = $Pharmacy_NCPDPs{$pharmacy_id};

       &send_ach_email($pharmacy_id, $ncpdp, $acct_mgr, $contact_name, $contact_email, $tpp, $pmt_meth, $pmt_amt, $pmt_dte);
       &create_intervention($pharmacy_id, $acct_mgr, $tpp_id, $chk_num);
     }

     &logActivity($LOGIN, "$Pharmacy_Name (via $PostedByUser) marked check id $Check_ID as $PENDRECV_SAVE", $PH_STRING) if ( $NumOfRows2 >= 1 );
  }
}

#______________________________________________________________________________

sub send_ach_email {
  my $ph_id    = shift @_;
  my $NCPDP    = shift @_;
  my $ram      = shift @_;
  my $pc_name  = shift @_;
  my $pc_email = shift @_;
  my $tpp      = shift @_;
  my $pmt_meth = shift @_;
  my $pmt_amt  = shift @_;
  my $pmt_dte  = shift @_;
  my $sig_img  = 'D:\\WWW\\members.recon-rx.com\\images\\Outcomes_ReconRx_sig.png';
#  print "Sending ACH Notification - $ph_id, $NCPDP, $ram, $pc_name, $pc_email, $tpp, $pmt_meth, $pmt_amt, $pmt_dte<br>\n";

  my $USER = $CSR_IDs{$ram};

  @pcs = split(/,/, $ram);
  $ram_name = "$pcs[1] $pcs[0]";

  @pcs = split(/@/, $CSR_Emails{$ram});
  $user_email = $pcs[0];
  $from = $user_email;

  $to      = $pc_email;
  $to_name = $pc_name;
#  print "SEND: $to -> $to_name FROM: $from<br>\n";

#  $to   = 'CW_BProwell@tdsclinical.com';

  my $message = "<style>p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0in; margin-bottom:.0001pt; font-size:11.0pt; font-family:\\'Calibri\\',sans-serif;} table.bd, td.bd, th.bd {
  border: 1px solid black; padding: 5px;}</style>";

  $subject = "ReconRx Action Required: Bank Letter Needed for Missing ACH Payment NCDPD - $NCPDP";

  $message .= "<p>$pc_name,</p><p>Please provide a letter from your bank stating that the ACH payment associated with the pending remit you marked as missing below was not deposited into your account. Once your letter from the bank is received, I will send this missing payment to the third party payer to research. As always, please do not hesitate to contact me if you have any questions.</p>";
  $message .= "<table class=\\'bd\\' style=\\'border-collapse: collapse;\\'><tr><th class=\\'bd\\'>Payer</th><th class=\\'bd\\'>Amount</th><th class=\\'bd\\'>Date</th></tr>";
  $message .= "<tbody><tr><td class=\\'bd\\'>$tpp</td><td class=\\'bd\\'>$pmt_amt</td><td class=\\'bd\\'>$pmt_dte</td></tr></tbody></table>";

  #### Insert into MAM
  $sql = "INSERT INTO reconrxdb.communication (pharmacy_id, user_id, `name`, subject, status, automated)
          VALUES ($ph_id, $USER, '', '$subject', 'N', 1)";

#  print "COMM Master SQL:\n$sql<br>\n";

  $inserted = $dbz->do($sql) or die $DBI::errstr;

  if ( $inserted == 1 ) {
    $sth = $dbz->prepare("SELECT LAST_INSERT_ID()") || die "Error preparing query" . $dbz->errstr;
    $sth->execute() or die $DBI::errstr;
    $comm_id = $sth->fetchrow_array();
    $sth->finish();

    $sql = "INSERT INTO reconrxdb.communication_dtl (comm_id, user_id, status, message)
             VALUES ($comm_id, $USER, 'N', '$message')"; 

#    print "COMM Detail SQL:\n$sql<br>\n";

    $inserted = $dbz->do($sql) or die $DBI::errstr;
  }

  $message =~ s/\\//g;

  $message .= &add_email_sig($ram, $user_email);

  if ( $to ) {
    $retval = &send_email($from, $to, $subject, $message, 1, $sig_img);
  }
}

#______________________________________________________________________________

sub add_email_sig {
  my $ram = shift @_;
  my $user = shift @_;
  my $display = shift @_;
  my $sig_img;

  if ( $display =~ /Web/i ) {
    $sig_img   = "../images/Outcomes_ReconRx_sig.png";
  }
  else {
    $sig_img   = "cid:Outcomes_ReconRx_sig.png";
  }

  @pcs = split(/\,\s/, $ram);
  $sig_name = "$pcs[1] $pcs[0]";
  $sig_email = $EMAILACCT{$user};
  $sig_title = $EMAIL_SIG_TITLE{$user};
  $sig_ext   = $EMAIL_SIG_EXT{$user};

  my $sig .= "<p>Thank You,</p><table>
                <tr>
                  <td style='background:white;padding:0in 6.0pt 0in 6.0pt'>
                    <b><span style='font-size:12.0pt;color:#002060;text-transform:uppercase'>$sig_name</span></b><br>
                    <span style='color:#002060;text-transform:uppercase'>$sig_title<br></span>
                  </td>
                <tr>
                  <td>
                    <img border=0 width=255 height=133 src='cid:Outcomes_ReconRx_sig.png' align=left hspace=12>
                  </td>
                </tr>
                <tr>
                  <td style='background:white;padding:0in 1.0pt 0in 1.0pt'>
                    <span style='color:blue'><a href='mailto:$sig_email'>$sig_email</a></span></br>
                    <span style='color:#002060;text-transform:uppercase'>TEL: (888) 255-6526 ext. 118</span></br>
                    <p class=MsoNormal style='mso-margin-top-alt:auto;line-height:105%'>
                      <span style='font-size:9.0pt;line-height:105%;color:#767171'>
                        The information contained in this transmission may contain privileged and confidential information, including patient information protected by federal and state privacy laws. It is intended only for the use of the person(s) named above. If you are not the intended recipient, you are hereby notified that any review, dissemination, distribution, or duplication of this communication is strictly prohibited. If you are not the intended recipient, please contact the sender by reply email and destroy all copies of the original message.
                      </span>
                    </p>
                  </td>
                </tr>
              </table>";

  return $sig;
}

#______________________________________________________________________________

sub create_intervention {
  my $Pharmacy_ID = shift @_;
  my $acct_mgr    = shift @_;
  my $tpp_id      = shift @_;
  my $checks      = shift @_;

#  chop($checks);

  my $open_date = &build_date();
  my $open_date_TS = &build_date_TS($open_date);
  my ($type_id, $cat, $type, $comments);

  $type     = 'ThirdPartyPayer';
  $type_id  = $tpp_id; 
  $cat      = 'ReconRx - Missing CHK';
  $comments = 'A bank letter has been requested from the pharmacy for the missing ACH: ' . $checks;

  my $sql = "INSERT 
               INTO officedb.interventions 
                SET Pharmacy_ID = $Pharmacy_ID,
                    Type = '$type',
                    Type_ID = '$type_id',
                    Category = '$cat',
                    Program = 'ReconRx',
                    CSR_ID = $CSR_IDs{$acct_mgr},
                    CSR_Name = '$acct_mgr',
                    Status = 'Active',
                    Opened_Date_TS = '$open_date_TS',
                    Opened_Date = '$open_date',
                    Comments = '$comments'";

#  print "$sql<br>";

  my $sth = $dbz->prepare($sql);
  $sth->execute() or die $DBI::errstr;
  $inserted = $sth->rows;

  $sth->finish();
}
