require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; 
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$inTPP      = $in{'inTPP'};
$inNCPDP    = $in{'NCPDPNumber'};
$SORT       = $in{'SORT'};
$inFrmDate  = $in{'frm_date'};
$inToDate   = $in{'to_date'};

$inNCPDP = substr($inNCPDP,0,7);

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

$fNCPDP = sprintf("%07d", $inNCPDP);
$ph_id  = $Reverse_Pharmacy_NCPDPs{$fNCPDP};
$ph_id  = 0 if (!$ph_id);

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
$CHECKYEAR = $year + 1;
$DATEEX = sprintf("%02d/%02d/%04d", $month, $day, $year);

#______________________________________________________________________________


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

&readThirdPartyPayers;
&readTPPPriSec;
&readReconExceptionRouting;
&readReconExceptionRouting2;

$dbin    = "RIDBNAME";  # Only database needed for this routine
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};
$FIELDS  = $DBFLDS{"$dbin"};
$FIELDS2 = $DBFLDS{"$dbin"} . "2";
$prefix  = "RI";	# unique to this table

$FMT = "%0.02f";
my $TPP_Count = 0;
my $sixmonths = 6 * 30 * 24 * 60 * 60;

my %RParentkeys;
my %RBINs;
my %RTPP_Names;
my %RTotals;
my %RTotalPPs;
my %RF1to44s;
my %RF45to59s;
my %RF60to89s;
my %RFover90s;

my %Grand_RTotals;
my %Grand_RTotalPPs;
my %Grand_RF1to44s;
my %Grand_RF45to59s;
my %Grand_RF60to89s;
my %Grand_RFover90s;

#---------------------------------------
# Connect to the database

  $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
         { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
  DBI->trace(1) if ($dbitrace);
#---------------------------------------

if ( $in{'incoming_id'} && $in{'btnSubmit'} eq 'Save') {
  &update_data();
  $inFrmDate  = '';
  $inToDate   = '';
}

if ( $inTPP ) {
   print qq#<a class="text_navy" href="javascript:history.go(-1)"> Go Back</a><br>\n#;
   &displaySingleTPP($inTPP, $inNCPDP);
} else {
   print qq#<h1 class="page_title">Claims Research</h1>\n#;
   print "<hr>\n";

   &displayWebPage;
}

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

#  ($PROG = $prog) =~ s/_/ /g;

  my $found  =  0;
  my %JSTART = ();
  my %JEND   = ();

#  $DateRanges{1} =  0;
  $DateRanges{1} = 45;
  $DateRanges{2} = 60;
  $DateRanges{3} = 90;

  foreach $DR (sort { $a <=> $b } keys %DateRanges) {
     $DRNext = $DR + 1;
     my $start;
     my $end;
     if ( $DR == 3 ) {
        $start = $DateRanges{$DR};
        $end   = $DateRanges{$DRNext} + 10000;

     } else {
        $start = $DateRanges{$DR};
        $end   = $DateRanges{$DRNext} - 1;
     }
     ($qstart, $qend) = &calcRanges($start, $end);
     $JSTART{$DR} = $qstart;
     $JEND{$DR}   = $qend;
  }

#-----------------------------------------------------------------------------------------------------

  print qq#<form id="selectForm" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print "<table>\n";

  print qq#<tr><th><label for="NCPDPNumber">Pharmacy:</label></th>#;
  print qq#<th><input type="text" name="NCPDPNumber" list="plist" id="NCPDP" value="$inNCPDP" style="width:300px;">\n#;
  print qq#<datalist id="plist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
               FROM officedb.pharmacy 
              WHERE (Status_ReconRx IN ('Active','Transition') OR Status_ReconRx_Clinic IN ('Active','Transition'))
                 && NCPDP NOT IN (2222222,3333333,5555555)
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE (Status_ReconRx IN ('Active','Transition') OR Status_ReconRx_Clinic IN ('Active','Transition'))
                 && NCPDP NOT IN (2222222,3333333,5555555)
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($ph_id, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
  }

  $sthx->finish;
  print qq#</datalist>&nbsp;<INPUT class="button-form" TYPE="submit" NAME="Select" VALUE="Search"></th></tr></table>#;

#-----------------------------------------------------------------------------------------------------

  if ( $inNCPDP ) {
    
    $ph_id = $Reverse_Pharmacy_NCPDPs{$fNCPDP};

    $ntitle = "Aging Report";
    print qq#<h1 class="page_title">$ntitle</h1>\n#;

    &getData($ph_id);

    $columnWidth  = 100;
    print qq#<table class="main">\n#;

    print qq#</tr>\n#;
    print qq#<tr>#;
    print qq#<th $col1width class="align_left lj_blue_bb">Third Party</th>#;
    print qq#<th class="align_right lj_blue_bb">Total</th>#;

    foreach $DR (sort { $a <=> $b } keys %DateRanges) {
       $DRNext = $DR + 1;
       $start = $DateRanges{$DR};
       $end   = $DateRanges{$DRNext} - 1;
       if ( !$start ) {
          print qq#<th class="align_right lj_blue_bb" width=$columnWidth>1-$end</th>#;
       } else {
          if ( $DR == 3 ) {
             print qq#<th class="align_right lj_blue_bb" width=$columnWidth>$DateRanges{$DR}+</th>#;
          } else {
             print qq#<th class="align_right lj_blue_bb" width=$columnWidth>$start-$end</th>#;
          }
       }
    }
    print qq#</tr>\n#;

    $row = 0;
    foreach $key ( sort { $RTPP_Names{$a} cmp $RTPP_Names{$b} } keys %RTPP_Names ) {
      $Parentkey = $RParentkeys{$key};
      $TPP_Name  = $RTPP_Names{$key};
      $Total     = "\$" . &commify(sprintf("$FMT", $RTotals{$key}));
      $TotalPP   = "\$" . &commify(sprintf("$FMT", $RTotalPPs{$key}));
      $F1to44    = "\$" . &commify(sprintf("$FMT", $RF1to44s{$key}));
      $F45to59   = "\$" . &commify(sprintf("$FMT", $RF45to59s{$key}));
      $F60to89   = "\$" . &commify(sprintf("$FMT", $RF60to89s{$key}));
      $Fover90   = "\$" . &commify(sprintf("$FMT", $RFover90s{$key}));
	
      if (0 == $row % 2) {
        $rowclass = "lj_blue_table";
      } else {
        $rowclass = "";
      }

      print qq#<tr>#;
      print qq#<td class="$rowclass"><a class="$rowclass" href="${prog}.cgi?inTPP=${Parentkey}&NCPDPNumber=$inNCPDP">$TPP_Name</a></td>#;

      print qq#<td align=right class="$rowclass">$TotalPP </td>#;
      print qq#<td align=right class="$rowclass">$F45to59</td>#;
      print qq#<td align=right class="$rowclass">$F60to89</td>#;
      print qq#<td align=right class="$rowclass">$Fover90</td>#;
      print qq#</tr>\n#;
      $TPP_Count++;
      $row++;
    }

#-----------------------------------------------------------------------

    &displaySwitchData($ph_id);
    print qq#</table>\n#;
  }
}

#______________________________________________________________________________

sub displaySwitchData {
  $ph_id = shift @_;
  $savebin    =  0;
  $savekey    =  0;
  %slots      = ();

  $Grand_RTotals   = "\$" . &commify(sprintf("$FMT", $Grand_RTotals));
  $Grand_RTotalPPs = "\$" . &commify(sprintf("$FMT", $Grand_RTotalPPs));
  $Grand_RF1to44s  = "\$" . &commify(sprintf("$FMT", $Grand_RF1to44s));
  $Grand_RF45to59s = "\$" . &commify(sprintf("$FMT", $Grand_RF45to59s));
  $Grand_RF60to89s = "\$" . &commify(sprintf("$FMT", $Grand_RF60to89s));
  $Grand_RFover90s = "\$" . &commify(sprintf("$FMT", $Grand_RFover90s));

  print qq#<tr>#;
  print qq#<th class="lj_blue_bt">Grand Totals</th>#;
  print qq#<th class="money lj_blue_bt" bgcolor=yellow>$Grand_RTotals</th># if ($LOCENV =~ /Dev/i);
  print qq#<th class="money lj_blue_bt">$Grand_RTotalPPs</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RF45to59s</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RF60to89s</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RFover90s</th>#;
  print qq#</tr>\n#;

  if ( $TPP_Count <= 0 ) {
    print qq#<tr><th class="yellow" colspan=7>No Records found for $Pharmacy_Name</th></tr>#;
  }
}

#______________________________________________________________________________

sub displaySingleTPP {
  my ($inTPP, $NCPDP) = @_;
  my $ph_id    = $Reverse_Pharmacy_NCPDPs{$NCPDP};
  my $Pharmacy_Name = $Pharmacy_Names{$ph_id};
  my $inBIN    = $TPP_BINs{$inTPP};
  my $inTPPNme = $ThirdPartyPayer_Names{$inTPP};
  my $all_check = '';
  my $g_check = '';
  my $y_check = '';
  my $r_check = '';
  $DBNAME = 'webinar' if ($ph_id ==23);

  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;

  print << "JDO";
  <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
  <script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
  <script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>

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

  $URLH = "${prog}.cgi";
  print qq#<FORM  name="frm2" id="frm2" ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inTPP"    VALUE="$inTPP">\n#;
  print qq#<INPUT TYPE="hidden" NAME="remit_id" VALUE="">\n#;
  print qq#<INPUT TYPE="hidden" NAME="NCPDPNumber" VALUE="$in{'NCPDPNumber'}">\n#;
  print qq#<INPUT TYPE="hidden" NAME="incoming_id" VALUE="">\n#;

  if ( $in{'claim_type'} =~ /All/i ) {
    $all_check = 'checked';
  }
  elsif ( $in{'claim_type'} =~ /Green/i ) {
    $g_check = 'checked';
  }
  elsif ( $in{'claim_type'} =~ /Yellow/i ) {
    $y_check = 'checked';
  }
  elsif ( $in{'claim_type'} =~ /Red/i ) {
    $r_check = 'checked';
  }
  else {
    $all_check = 'checked';
    $in{'claim_type'} = 'All';
  }


  #jQuery now loaded on all pages via header include.
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq#\$(document).ready(function() { \n#;
  print qq#                \$('\#tablef').dataTable( { \n#;
  print qq#                                "sScrollX": "100%", \n#;
  print qq#                                "bScrollCollapse": true,  \n#;
  print qq#                                "aaSorting": [ [4,'asc'] ], \n#;
  print qq#                                "sScrollY": "350px", \n#;
  print qq#                                "bPaginate": false \n#;
  print qq#                } ); \n#;
  print qq#} ); \n#;
  print qq# function checkAll(ele) { \n#;
  print qq#     var checkboxes = document.getElementsByTagName('input'); \n#;
  print qq#     if (ele.checked) { \n#;
  print qq#         for (var i = 0; i < checkboxes.length; i++) { \n#;
  print qq#             if (checkboxes[i].type == 'checkbox') { \n#;
  print qq#                 checkboxes[i].checked = true; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#     } else { \n#;
  print qq#         for (var  i = 0; i < checkboxes.length; i++) { \n#;
  print qq#             if (checkboxes[i].type == 'checkbox') { \n#;
  print qq#                 checkboxes[i].checked = false; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#     } \n#;
  print qq# } \n#;
  print qq# function setSelected(form) { \n#;
  print qq#     var ids = ''; \n#;
  print qq#     if ( \$("\#cscode").val() != '' ) {  \n#;
  print qq#       for (var i = 0; i < form.elements.length; i++ ) { \n#;
  print qq#         if (form.elements[i].type == 'checkbox' && form.elements[i].name == 'ids') { \n#;
  print qq#             if (form.elements[i].checked == true) { \n#;
  print qq#                 ids += form.elements[i].value + ','; \n#;
  print qq#             } \n#;
  print qq#         } \n#;
  print qq#       } \n#;
  print qq#     } else { \n#;
  print qq#       alert('Code Not Selected'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq#     ids = ids.substring(0, ids.length - 1); \n#;
  print qq#     if (ids == '') { \n#;
  print qq#       alert('No Records Selected'); \n#;
  print qq#       return false; \n#;
  print qq#     } \n#;
  print qq#     form.incoming_id.value = ids\n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print qq#<br>\n#;
  print qq#<span style="font-weight: bold">Pharmacy: $Pharmacy_Name - $NCPDP</span><br>\n#;
  print qq#<span style="font-weight: bold">TPP: $inTPPNme</span><br>\n#;
  print qq#<br>\n#;
  print qq#<font size=-1><i>Codes: NP-Non Payment, PP-Partial Payment</i></font><br>\n#;
  print qq#<input type="radio" name="claim_type" id="all" value="All" $all_check onchange="form.submit();"><label form="all">All</label>&nbsp;#;
  print qq#<input type="radio" name="claim_type" id="green" value="Green" $g_check onchange="form.submit();"><label form="green" style="color: green">Green</label>&nbsp;#;
  print qq#<input type="radio" name="claim_type" id="yellow" value="Yellow" $y_check onchange="form.submit();"><label form="yellow" style="color: \#FFBD33">Yellow</label>&nbsp;#;
  print qq#<input type="radio" name="claim_type" id="red" value="Red" $r_check onchange="form.submit();"><label form="red" style="color: red">Red</label>#;

  $UpDB_CheckDate = "";
  print qq#</br>From: #;
  print qq#<INPUT CLASS="datepicker check_date" TYPE="text" NAME="frm_date" VALUE="$inFrmDate" SIZE=10 MAXLENGTH=10>#;
  print qq#$nbsp To: #;
  print qq#<INPUT CLASS="datepicker check_date" TYPE="text" NAME="to_date" VALUE="$inToDate" SIZE=10 MAXLENGTH=10> $nbsp #;
  print qq#<INPUT style="margin:5px" TYPE="submit" NAME="btnSubmit" VALUE="Update">\n#;

  ## CS Codes
  print "<div style='display: inline-block; float: right; width: auto; border: 1px solid;'>";
  print "<div style='text-align: center; font-weight: bold; background-color: #133562; color: white; padding: 2px;'>Bulk Update</div>
         <div style='padding: 3px;'>
              <select name='cscode' id='cscode'>
                       <option value=''>-Select-</option>";

  $sql = "SELECT code, dscr
            FROM reconrxdb.cscodes
        ORDER BY dscr";

#  print "$sql<br>";

  my $sth    = $dbx->prepare("$sql");
  my $numrows = $sth->execute();
	
  while( my ($code, $dscr) = $sth->fetchrow_array() ) {
    print "<option value='$code'>$dscr</option>";
  }

  $sth->finish();

  print "</select>\n";
  ##

  print qq#<INPUT style="margin:5px" TYPE="submit" NAME="btnSubmit" VALUE="Save" onclick="return setSelected(document.frm2)"></br>\n#;
  print "</div></div>";


  print qq#<table id="tablef">\n#;

  print qq#<thead>\n#;
  print qq#<tr>
             <th>BIN</th>
             <th>PCN</th>
             <th>Rx</th>
             <th>Filled Date</th>
             <th>Processed Date</th>
             <th>Amount Due</th>
             <th>Code</th>
             <th>Date Sent</th>
             <th><INPUT name=\"selectall\" type=\"checkbox\" onchange=\"checkAll(this)\" name=\"ids[]\" /></th>\n#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;

  my $TotalPaidPP = 0;

  my $date_filter = '';

  if ( $inFrmDate && $inToDate ) {
    @pcs = split('/', $inFrmDate);
    $inFrmDate = sprintf("%04d%02d%02d", $pcs[2], $pcs[0], $pcs[1]);
    $inFrmDate .= '000000';
    @pcs = split('/', $inToDate);
    $inToDate = sprintf("%04d%02d%02d", $pcs[2], $pcs[0], $pcs[1]);
    $inToDate .= '235959';
    $date_filter = "AND dbDateTransmitted >= '$inFrmDate' AND dbDateTransmitted <= '$inToDate'";
  }
  if ( $in{'claim_type'} =~ /All|Green/i ) {
    my $sql = "";

    ### Green Record Select
    $sql = "SELECT rmt.835remitstbID, clm.dbBinNumber, clm.dbRxNumber, Date_Format(clm.dbDateOfService,'%m/%d/%Y'), Date_Format(SUBSTR(clm.dbDateTransmitted,1,8),'%m/%d/%Y'),
                   IFNULL(clm.dbTotalAmountPaid_Remaining,0), IFNULL(clm.dbTotalAmountPaid,0), clm.dbProcessorControlNumber, clm.dbCode, Date_Format(prr.Notice_Sent,'%m/%d/%Y')
              FROM $DBNAME.incomingtb clm
              JOIN $DBNAME.835remitstb rmt ON (clm.pharmacy_id = rmt.pharmacy_id
                                          AND clm.dbRxNumber = rmt.R_CLP01_Rx_Number
                                          AND clm.dbDateOfService = rmt.R_DTM02_Date
                                          AND clm.dbTotalAmountPaid_Remaining = rmt.R_CLP04_Amount_Payed)
              JOIN reconrxdb.checks chk ON (rmt.Check_ID = chk.Check_ID)
  	      LEFT JOIN reconrxdb.pending_remit_reminder prr ON (rmt.pharmacy_id = prr.pharmacy_id
                                                            AND chk.R_TPP_PRI = prr.tpp_id
                                                            AND chk.R_BPR04_Payment_Method_Code = prr.Payment_Method_Code
                                                            AND chk.R_BPR02_Check_Amount = prr.Check_Amount
                                                            AND chk.R_BPR16_Date = prr.Check_Date)
             WHERE chk.R_PENDRECV='P'
               AND clm.pharmacy_id = $ph_id
               AND clm.dbBinParentdbkey = $inTPP
               AND clm.dbCode <> 'PD'
               AND DATE(LEFT(clm.dbDateTransmitted,8)) <= (CURDATE() - INTERVAL 45 DAY)
               AND (dbTCode = '' || dbTCode = 'PP')
          ORDER BY clm.dbRxNumber";

    ($sqlout = $sql) =~ s/\n/<br>\n/g;
    print "<hr>1. sql:<br>$sql<hr>\n" if ($debug);

    $sthrp = $dbx->prepare($sql);
    $sthrp->execute();
    my $numofrows = $sthrp->rows;

    while ( my ( $id, $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbProcessorControlNumber, $dbCode, $date_sent ) = $sthrp->fetchrow_array()) {
      next if ( $dbTotalAmountPaid == -20000);
      next if ( $dbTotalAmountPaid == 0);

      print qq#<tr style="color: Green;">#;

      print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
      print qq#<td>$dbProcessorControlNumber</td>#;
      print qq#<td>$dbRxNumber</td>#;
      print qq#<td>$dbDateOfService</td>#;
      print qq#<td>$dbDateTransmitted</td>#;
      print qq#<td class="align_right">\$$dbTotalAmountPaid_Remaining</td>#;
      print qq#<td class="align_center">$dbCode</td>#;
      print qq#<td class="align_center">$date_sent</td>#;
      print qq#<td class="align_center">$nbsp</td>#;
      print qq#</tr>\n#;
      $TotalPaidPP += $dbTotalAmountPaid_Remaining;
    }

    $sthrp->finish;
  }

  if ( $in{'claim_type'} =~ /All|Red/i ) {
    ### Red Record Select
    $sql = "SELECT * FROM (
            SELECT clm.incomingtbID, rmt.835remitstbID, clm.dbBinNumber, clm.dbRxNumber, Date_Format(clm.dbDateOfService,'%m/%d/%Y'), Date_Format(SUBSTR(clm.dbDateTransmitted,1,8),'%m/%d/%Y'),
                   IFNULL(clm.dbTotalAmountPaid_Remaining,0), IFNULL(clm.dbTotalAmountPaid,0), clm.dbProcessorControlNumber, clm.dbCode, ''
              FROM $DBNAME.incomingtb clm
         LEFT JOIN (SELECT b.*
                      FROM $DBNAME.Checks a
                      JOIN $DBNAME.835remitstb b ON (a.Check_ID = b.Check_ID)
                     WHERE b.Pharmacy_ID = $ph_id
                       AND a.R_PENDRECV='P'
                   ) rmt ON (clm.pharmacy_id = rmt.pharmacy_id
                            AND clm.dbRxNumber = rmt.R_CLP01_Rx_Number
                            AND clm.dbDateOfService = rmt.R_DTM02_Date
                            AND clm.dbTotalAmountPaid_Remaining = rmt.R_CLP04_Amount_Payed)
             WHERE clm.pharmacy_id = $ph_id
               AND clm.dbBinParentdbkey = $inTPP
               AND clm.dbCode NOT IN ('PD','FRR')
               AND DATE(LEFT(clm.dbDateTransmitted,8)) <= (CURDATE() - INTERVAL 45 DAY)
               AND (dbTCode = '' || dbTCode = 'PP')
                   $date_filter
          ORDER BY clm.dbRxNumber) x WHERE 835remitstbID IS NULL";

    ($sqlout = $sql) =~ s/\n/<br>\n/g;
    print "<hr>1. sql:<br>$sql<hr>\n" if ($debug);

    $sthrp = $dbx->prepare($sql);
    $sthrp->execute();
    my $numofrows = $sthrp->rows;

    while ( my ( $id, $rid, $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbProcessorControlNumber, $dbCode, $date_sent ) = $sthrp->fetchrow_array()) {
      next if ( $dbTotalAmountPaid == -20000);
      next if ( $dbTotalAmountPaid == 0);

      print qq#<tr style="color: Red;">#;

      print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
      print qq#<td>$dbProcessorControlNumber</td>#;
#      print qq#<td><a style="color: red;" href="" onclick="window.open( 'detail_search.cgi?PH_ID=$ph_id&rxnumber=$dbRxNumber', '_blank', 'opener,height=750,width=1000' ); return false">$dbRxNumber</a></td>#;
      print qq#<td><a style="color: red;" href="detail_search.cgi?PH_ID=$ph_id&rxnumber=$dbRxNumber" target="_blank" rel="opener">$dbRxNumber</a></td>#;
#      print qq#<td><a style="color: red;" href="detail_search.cgi?PH_ID=$ph_id&rxnumber=$dbRxNumber">$dbRxNumber</a></td>#;
      print qq#<td>$dbDateOfService</td>#;
      print qq#<td>$dbDateTransmitted</td>#;
      print qq#<td class="align_right">\$$dbTotalAmountPaid_Remaining</td>#;
      print qq#<td class="align_center">$dbCode</td>#;
      print qq#<td class="align_center">$date_sent</td>#;
      if ( $dbCode =~ /NP|PP/ ) {
        print qq#<td><input type='checkbox' name='ids' value=$id></td>#;
      }
      else {
        print qq#<td class="align_center">$nbsp</td>#;
      }
      print qq#</tr>\n#;
      $TotalPaidPP += $dbTotalAmountPaid_Remaining;   
    }

    $sthrp->finish;
  }

  if ( $in{'claim_type'} =~ /All|Yellow/i ) {
    ### Yellow Record Select
    $sql = "SELECT * FROM (
            SELECT clm.incomingtbID, rmt.835remitstbID, clm.dbBinNumber, clm.dbRxNumber, Date_Format(clm.dbDateOfService,'%m/%d/%Y'), Date_Format(SUBSTR(clm.dbDateTransmitted,1,8),'%m/%d/%Y'),
                   IFNULL(clm.dbTotalAmountPaid_Remaining,0), IFNULL(clm.dbTotalAmountPaid,0), clm.dbProcessorControlNumber, clm.dbCode, ''
              FROM $DBNAME.incomingtb clm
         LEFT JOIN (SELECT b.*
                      FROM $DBNAME.Checks a
                      JOIN $DBNAME.835remitstb b ON (a.Check_ID = b.Check_ID)
                     WHERE b.Pharmacy_ID = $ph_id
                       AND a.R_PENDRECV='P'
                   ) rmt ON (clm.pharmacy_id = rmt.pharmacy_id
                            AND clm.dbRxNumber = rmt.R_CLP01_Rx_Number
                            AND clm.dbDateOfService = rmt.R_DTM02_Date
                            AND clm.dbTotalAmountPaid_Remaining = rmt.R_CLP04_Amount_Payed)
             WHERE clm.pharmacy_id = $ph_id
               AND clm.dbBinParentdbkey = $inTPP
               AND clm.dbCode = 'FRR'
               AND DATE(LEFT(clm.dbDateTransmitted,8)) <= (CURDATE() - INTERVAL 45 DAY)
               AND (dbTCode = '' || dbTCode = 'PP')
                   $date_filter
          ORDER BY clm.dbRxNumber) x WHERE 835remitstbID IS NULL";

    ($sqlout = $sql) =~ s/\n/<br>\n/g;
    print "<hr>1. sql:<br>$sql<hr>\n" if ($debug);

    $sthrp = $dbx->prepare($sql);
    $sthrp->execute();
    my $numofrows = $sthrp->rows;

    while ( my ( $id, $rid, $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbProcessorControlNumber, $dbCode, $date_sent ) = $sthrp->fetchrow_array()) {
      next if ( $dbTotalAmountPaid == -20000);
      next if ( $dbTotalAmountPaid == 0);

      print qq#<tr style="color: \#FFBD33;">#;

      print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
      print qq#<td>$dbProcessorControlNumber</td>#;
#      print qq#<td><a style="color: \#FFBD33;" href="" onclick="window.open( 'detail_search.cgi?PH_ID=$ph_id&rxnumber=$dbRxNumber', '_blank', 'opener,height=750,width=1000' ); return false">$dbRxNumber</a></td>#;
      print qq#<td><a style="color: \#FFBD33;" href="detail_search.cgi?PH_ID=$ph_id&rxnumber=$dbRxNumber" target="_blank">$dbRxNumber</a></td>#;
#      print qq#<td>$dbRxNumber</td>#;
      print qq#<td>$dbDateOfService</td>#;
      print qq#<td>$dbDateTransmitted</td>#;
      print qq#<td class="align_right">\$$dbTotalAmountPaid_Remaining</td>#;
      print qq#<td class="align_center">$dbCode</td>#;
      print qq#<td class="align_center">$date_sent</td>#;
      if ( $dbCode =~ /NP|PP|FRR/ ) {
        print qq#<td><input type='checkbox' name='ids' value=$id></td>#;
      }
      else {
        print qq#<td class="align_center">$nbsp</td>#;
      }
      print qq#</tr>\n#;
      $TotalPaidPP += $dbTotalAmountPaid_Remaining;   
    }

    $sthrp->finish;
  }
 
  print qq#</tbody>\n#;
  $TotalPaidPP = "\$" . &commify(sprintf("$FMT", $TotalPaidPP));
  print qq#<tr>#;
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>#;


  print qq#<div style="text-align: right; font-weight: bold; padding-right: 15px">\n#;

  print qq#Grand Total: $TotalPaidPP<br>\n#;

  print qq#</div>\n#;

  print qq#</FORM>\n#;
}

#______________________________________________________________________________

sub getData {
  $ph_id = shift @_;
  $display_esi = '';

  if ($Pharmacy_DisplayESI{$ph_id} =~ /^Y$/) {
     $display_esi = 1;
     ##$TPP_Reconciles{'700006'} = 'Yes';
  }
    
  $reconrx_aging_sql = &get_reconrx_aging_sql($ph_id,$display_esi);

  my $sql =" SELECT TPP_ID, dbBinNumber, Third_Party_Payer_Name, sum(dbTotalAmountPaid_Remaining) as 'Total', sum(`1-44 Days`) as a, sum(`45-59 Days`) as b, sum(`60-89 Days`) as c ,sum(`90+ Days`) as d 
             FROM ($reconrx_aging_sql
                  )a
            GROUP BY TPP_ID";

#  print "$sql<br>";

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while ( my ($Parentkey, $BIN, $TPP_Name, $TotalPP, $F1to44, $F45to59, $F60to89, $Fover90) = $sthrp->fetchrow_array()) {
     next if ( $Parentkey == -1 );

     my $keyBinNumber = $dbBinParents{$Parentkey} || $BIN;
     my $TPPID = "";    

     ##my ($jbin, $new_TPP_Name) = split("\-", $MyPrimary, 2);
     $TPP_Name     =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces

     $key = "$TPP_Name";

     $RParentkeys{$key}  = $Parentkey;
     $RBINs{$key}        = $BIN;
     $RTPP_Names{$key}   = $TPP_Name;
     $RTotals{$key}     += $Total;
     $RTotalPPs{$key}   += $TotalPP;
     $RF1to44s{$key}    += $F1to44;
     $RF45to59s{$key}   += $F45to59;
     $RF60to89s{$key}   += $F60to89;
     $RFover90s{$key}   += $Fover90;

     $Grand_RTotals     += $Total;
     $Grand_RTotalPPs   += $TotalPP;
     $Grand_RF1to44s    += $F1to44;
     $Grand_RF45to59s   += $F45to59;
     $Grand_RF60to89s   += $F60to89;
     $Grand_RFover90s   += $Fover90;

  }
  $sthrp->finish;
}

#______________________________________________________________________________

sub update_data {
  my ($key, $cscode, $sql);

  my $sel_ids = $in{'incoming_id'};
  my $code = $in{'cscode'};

  $sql  = "UPDATE $DBNAME.incomingtb
              SET dbCode = '$code'
            WHERE incomingtbID IN ($sel_ids)";

#   print "$sql<br>";
   $dbx->do($sql) or die $DBI::errstr;

   if ( $code =~ /FRR/i ) {
     $tcode = "'$code'";
   }
   else {
     $tcode = 'NULL';
   }

   @ids = split(',', $sel_ids);

   foreach $incoming_id (@ids) {
     $sql  = "REPLACE INTO $DBNAME.incomingtb_review (Pharmacy_ID, tpp_id, incomingtbID, cscode, status)
              VALUES ( $ph_id, $inTPP, $incoming_id, '$code', $tcode)";

#     print "$sql<br>";
     $dbx->do($sql) or die $DBI::errstr;
   }
}

#________________________________________
#;______________________________________
