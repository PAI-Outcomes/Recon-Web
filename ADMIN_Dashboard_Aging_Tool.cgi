require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;  

$| = 1; # don't buffer output

my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

@tables = ("incomingtb");

if ( $testing ) {
  $USEDBNAME = "testing";
} else {
  $USEDBNAME = "reconrxdb";
}

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

foreach $key (sort keys %in) {
  $$key = $in{$key};
}

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

&hasAccess($USER);

if ( $ReconRx_Admin_Dashboard_Aging_Tool !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;    # reported as "years since 1900".
$month += 1;    # reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%02d/%02d/%04d", $year, $month, $day, $year);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$long_time  = sprintf("%04d%02d%02d%02d%02d", $year, $month, $day, $hour, $min);

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong><br>\n#;

#______________________________________________________________________________

$opened_date_TS = time();
$opened_date    = sprintf("%04d-%02d-%02d %02d:%02d:%02d", $year, $month, $day, $hour, $min, 0);
$in_TPP_ID   = '';
$in_TPP_BIN  = '';
$in_TPP_NAME = '';
($in_TPP_ID, $in_TPP_BIN, $in_TPP_NAME) = split(" - ", $filter_in, 3);

#______________________________________________________________________________
#
($ENV) = &What_Env_am_I_in;
if ( $ENV =~ /^\s*$|DEV/i ) {
   $WEBPREFIX = "DEV";
} else {
   $WEBPREFIX = "WWW";
}

%SAVESQLS = ();
$SAVEINTS = "";

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#$problem_bin     = $in{'problem_bin'};

&readThirdPartyPayers;
($rScount) = &readSelected;
if ( $rScount ) {
   &processSelected;
}

&displayPage;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________
 
sub displayPage {
  print "<hr>\n";
  
  #DataTables style override
  print qq#<style>\n#;
  print qq#  table.dataTable tbody td, table.dataTable thead th {font-size: 10px !important;}\n#;
  print qq#</style>\n#;
  
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  #print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
  #Load DataTables externally
  print qq#<script type="text/javascript" charset="utf-8" src="https://cdn.datatables.net/1.10.2/js/jquery.dataTables.js"></script> \n#;

  print qq#
  <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
  <script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
  <script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>
  <script>
  
  //Execute the following only after the page has fully loaded.
  \$(function() {
  
    //Date formating options (relies on jQuery UI js and css files, as well as maskedinput file
    \$( ".datepicker" ).datepicker();
    \$( "\#anim" ).change(function() {
      \$( ".datepicker" ).datepicker( "option", "showAnim", \$( this ).val() );
    });
    \$(".datepicker").mask("99/99/9999");

    //Show or hide date range options based on selection.
    \$("input[name\$=daterange]").change(function() {
      var test = \$(this).val();
      \$(".hide").hide();
      \$("\#" + test).show();
    });
    \$("input[name\$=daterange]:checked").change();
    
    \$('.update_status').change(function() {
      if (\$(this).is(':checked')) {
        \$("\#text_input_status").show();
      } else {
        \$("\#text_input_status").hide();
      }
    });
    \$('.update_status').change();

    \$('.add_intervention').change(function() {
      if (\$(this).is(':checked')) {
        \$("\#text_input_intervention").show();
      } else {
        \$("\#text_input_intervention").hide();
      }
    });
    \$('.add_intervention').change();
    
    //Select all checkboxes code
    \$('\#selectallboxes').click(function(event) {  //on click
      if(this.checked) { // check select status
        \$('.checkboxes').each(function() { //loop through each checkbox
          this.checked = true;            
        });
      }else{
        \$('.checkboxes').each(function() { //loop through each checkbox
          this.checked = false;                  
        });        
      }
    });
    
    //Allow only 'mark' or 'remove' to be checked at any given time, never both.
    \$('.mark').click(function(event) {
      if(this.checked) {
        \$('.remove').each(function() {
        this.checked = false; 
      });
        }
    });
    \$('.remove').click(function(event) {
      if(this.checked) {
        \$('.mark').each(function() {
        this.checked = false; 
      });
        }
    });
    
    //copy status to textarea when clicked.
    \$('.status').click(function(event) {
      var edit = \$(this).text();
      \$('\#text_input_status').html(edit);
    });

//-------------------------------------------------------------------------------------------------------
// dataTable - Josh - 09/21/2015
//-------------------------------------------------------------------------------------------------------
  
    oTable = \$('\#tablef').dataTable( {
      autoWidth: false, 
      "sScrollX": "100%", 
      "bScrollCollapse": true, 
      //"sScrollY": "350px", 
      "bPaginate": false, 
      "aaSorting": [],
      "aoColumnDefs": [
        { 'bSortable': false, 'aTargets': [ 5,6 ] }
      ]
    }); 
    
  //On form submit (via \#submit_form button), clear filters using the fnResetAllFilters function, then IF checkData2 returns NOT FALSE, submit form
    \$("\#submit_form").click(function(e) {
      fnResetAllFilters(oTable);
    if (checkData2() != false) {
        \$('\#prform').submit();
    } else {
      oTable.fadeTo("fast", 1);
      //restore from faded state
    }
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

  };


//-------------------------------------------------------------------------------------------------------

  function checkData1() {
    if ( \$('\#daterange_range').is(':checked') && (\$('\#datefrom_value').val() == '' || \$('\#dateto_value').val() == '') ) {
      alert('If using "Range", you must set both dates!');
      return false;
    }
  }

  function checkData2() {
    if ( \$('.checkboxes').is(':checked') && \$('.action_options').is(':checked')) {
      //great
    } else {
      alert('Select at least one claim and choose an action.');
      return false;
    }
    if ( \$('.update_status').is(':checked') && \$('\#text_input_status').val() === '') {
      alert('No status has been entered to update!');
      return false;
    }
    if ( \$('.add_intervention').is(':checked') && \$('\#text_input_intervention').val() === '') {
      alert('No intervention has been entered to update!');
      return false;
    }
  }
  
  </script>
  #;
  
  print qq#<form action="$PROG" method="post" onsubmit="return checkData1()">#;
  
  # -------------------------------------------------------------------------------- #

  ($filterPCN) = &getFilterPayers($in_TPP_ID,$in_TPP_BIN,$in_TPP_NAME);

  my ($TPP_ID, $TPP_BIN, $TPP_NAME);

  print qq# <table class='noborders'><div><tr>
    <td><label for="TPP"> Third Party Payer: </label></td>
    <td><input type="text" name="filter_in" list="tpplist" id="tppname" value="$filter_in" style="width:250px;">
    <datalist id="tpplist" >#;
    foreach $key (sort { $filter_PayerNames{$a} cmp $filter_PayerNames{$b} } keys %filter_PayerNames) {
      my $TPP_ID   = $filter_PayerIDs{$key};
      my $TPP_BIN  = $filter_PayerBINs{$key};
      my $TPP_NAME = $filter_PayerNames{$key};
      print qq#<option value="$TPP_ID - $TPP_BIN - $TPP_NAME"> </option>\n#;
    }
  print qq# </datalist></td>#;

  &getFilterNCPDPs();

  print qq# 
    <td><label for="Pharmacy"> Pharmacy: </label></td>
    <td><input type="text" name="filter_ncpdp" list="pharmacy" id="pharmacyname" value="$filter_ncpdp" style="width:250px" autocomplete="off">
    <datalist id="pharmacy">#;
    foreach $key (sort { $filter_PharmacyNames{$a} cmp $filter_PharmacyNames{$b} } keys %filter_PharmacyNames) {
      my $NCPDP  = $filter_NCPDPs{$key};
      my $NAME   = $filter_PharmacyNames{$key};
      print qq#<option value="$key-$filter_NCPDPs{$key}-$filter_PharmacyNames{$key}"></option>\n#;
    }
  print qq#</datalist></td></tr></div></table>#;
  
  $CHECKED_all    = '';
  $CHECKED_range  = '';
  $CHECKED_45Plus = '';
  $CHECKED_pss    = '';
  $CHECKED_ALU    = '';
  
  if ($daterange      =~ /all/i) {
    $CHECKED_all      = 'CHECKED';
  } elsif ($daterange =~ /range/i) {
    $CHECKED_range    = 'CHECKED';
  } elsif ($daterange =~ /aged45Plus/i) {
    $CHECKED_45Plus   = 'CHECKED';
  } else {
    $CHECKED_45Plus   = 'CHECKED';
  }
  
  if ($filter_pss =~ /yes/i) {
    $CHECKED_pss   = 'CHECKED';
  }
  
  if ($filter_cfa =~ /yes/i) {
    $CHECKED_cfa   = 'CHECKED';
  }

  if ($show_ALU =~ /yes/i) {
    $CHECKED_ALU   = 'CHECKED';
  }
  
  print qq#<p>
  <input type="radio" name="daterange" id="daterange_45Plus"  value="aged45Plus" $CHECKED_45Plus> Aged 45+ Days <i>or</i>
  <input type="radio" name="daterange" id="daterange_range" value="Range"    $CHECKED_range> Date Range
  $nbsp $nbsp $nbsp Filter: 
  <input type="checkbox" name="filter_pss" value="Yes" $CHECKED_pss>PSS
  $nbsp
  <input type="checkbox" name="filter_cfa" value="Yes" $CHECKED_cfa>CFA
  $nbsp $nbsp Show: 
  <input type="checkbox" name="show_ALU" value="Yes" $CHECKED_ALU>Auto-Look-Up
  </p>\n#;
  
  my $datefromDisplay = $datefrom;
  my $datetoDisplay   = $dateto;
  if ($datefrom !~ /\//) {
    $datefromDisplay = substr($datefrom, 4, 2) . "/" . substr($datefrom, 6, 2) . "/" . substr($datefrom, 0, 4);
    $datetoDisplay = substr($dateto, 4, 2) . "/" . substr($dateto, 6, 2) . "/" . substr($dateto, 0, 4);
  }
  
  print qq#
  <div id="Range" class="hide" style="display: none;">
    <p>
      From: <INPUT class="datepicker" TYPE="text" NAME="datefrom" id="datefrom_value" VALUE="$datefromDisplay" > 
      $nbsp 
      To: <INPUT class="datepicker" TYPE="text" NAME="dateto" id="dateto_value" VALUE="$datetoDisplay" >
      $nbsp (Date of Service)
    </p>
  </div>
  #;
  
  print qq#<p><INPUT class="button-form" TYPE="submit" VALUE="Submit"></p>#;

  print qq#</form>#;
  
  print "<hr />\n";
  
  if ($filter_in !~ /^\s*$/ && $filter_in =~ /([0-9] - [0-9])/ ) {
    &displayDataWeb();
  } else { 
    print "<p>You must at least select a payer to continue</p>";
  }

  if ($show_ALU =~ /Yes/i) {
    # Auto Look Up
    &buildALU;
  }
}

#______________________________________________________________________________

sub displayDataWeb {
  my $DBNAME = $USEDBNAME;
  my $TABLE  = "incomingtb";
##  my $TABLE  = "incomingtb_unmatched_aged_claims";

  if ( $USEDBNAME =~ /testing/i ) {
     print "<hr>Don't forget to update $DBNAME.$TABLE<hr>\n";
  }

  my $sql = "SELECT dbNCPDPNumber, dbRxNumber, dbDateOfService, dbDateTransmitted, dbTotalAmountPaid, dbTCode,  dbStatus, dbPSS, dbCFA,
                    dbIntervention_ID, dbOtherPayerAmountRecognized, dbProcessorControlNumber, incomingtbID 
               FROM $DBNAME.$TABLE 
               JOIN ( SELECT *
                        FROM officedb.pharmacy
                       UNION
                      SELECT *
                        FROM officedb.pharmacy_coo
                    ) all_pharm
                 ON all_pharm.Pharmacy_ID = $TABLE.Pharmacy_ID
                 && Status_ReconRx = 'Active'
          LEFT JOIN reconrxdb.835remitstb
                   ON 1=1
                   && dbBinParent       = $in_TPP_BIN
                   && 835remitstb.Pharmacy_ID = $TABLE.Pharmacy_ID
                   && dbRxNumber        = R_CLP01_Rx_Number
                   && dbDateOfService   = R_DTM02_Date
                   && dbTotalAmountPaid = R_CLP04_Amount_Payed 
                   && dbTotalAmountPaid <> 0
              WHERE (1=1)
                 && R_TS3_NCPDP IS NULL
                 && dbBinParentdbkey      = $in_TPP_ID
                 && dbTotalAmountPaid > 0 ";

  $filter_ncpdp =~ s/^\s+//;
  if ($filter_ncpdp =~ /([0-9]-[A-Z0-9])/) {
   ($Pharmacy_ID, $selected_ncpdp, $pharm_name) = split("-", $filter_ncpdp, 3);
    $sql .= "&& $TABLE.Pharmacy_ID = $Pharmacy_ID";
  }
  else {
    $sql .= "&& $TABLE.Pharmacy_ID = 0";
  }
  
  if ($daterange =~ /45Plus/) {
    $sql .= "&& DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY)";
  }

  if ($datefrom !~ /^\s*$/ && $dateto !~ /^\s*$/ && $daterange =~ /range/i) {
    if ($datefrom =~ /\//) {
      my @pcs = split('/', $datefrom);    
      $datefrom = sprintf("%04d%02d%02d", $pcs[2], $pcs[0], $pcs[1]);
      @pcs = split('/', $dateto);    
      $dateto = sprintf("%04d%02d%02d", $pcs[2], $pcs[0], $pcs[1]);
    }
    $sql .= "&& DATE(dbDateTransmitted) >= $datefrom && DATE(dbDateTransmitted) <= $dateto\n";
  } 
  
  if ($filter_pss !~ /^\s*$/) {
    $sql .= "&& (dbPSS != '' && dbPSS IS NOT NULL)\n";
  }

  if ($filter_cfa !~ /^\s*$/) {
    $sql .= "&& (dbCFA != '' && dbCFA IS NOT NULL)\n";
  }
  
  $sql .= "ORDER BY dbNCPDPNumber, dbDateTransmitted";

  my $sthx  = $dbx->prepare("$sql");
  my $numrows = $sthx->execute;

  if ($numrows > 0) {
    print "<p>Filtering by <strong>TPPID</strong>: $in_TPP_ID, <strong>BIN:</strong> $in_TPP_BIN";
    print "<br>\n";
    print "The following claims are over 45 days old and have no potential remit matches.</p>\n";
    print qq#<form action="$PROG" method="post" name="prform" id="prform">#;
    print qq#<table id="tablef" class="main">\n#;
    print qq#<thead>\n#;
    print qq#
    <tr>
    <th><input type="checkbox" name="selectall" id="selectallboxes" value=""></th>
    <th>NCPDP</th>
    <th>Rx\#</th>
    <th>Fill Date</th>
    <th>Processed Date</th>
    <th>Amount Due</th>
    <th>TCode</th>
<!--
    <th>EVoucher</th>
-->
    <th>PSS</th>
    <th>CFA</th>
    <th>Int ID</th>
    <th>Status</th>
    </tr>\n#;

    print qq#</thead>\n#;
    print qq#<tbody>\n#;
    
    my $row = 1;
    
    while ( my @row = $sthx->fetchrow_array() ) {
      my ($dbNCPDPNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid, $TCode, $dbStatus, $dbPSS, $dbCFA, $dbIntervention_ID, $dbOtherPayerAmountRecognized, $dbProcessorControlNumber, $incomingtbID) = @row;
      
      $dbNCPDPNumber = sprintf("%07d", $dbNCPDPNumber);

      $SAVEINTS .= "$dbIntervention_ID, " if ( $dbIntervention_ID !~ /^\s*$/ );

##      if ( $dbOtherPayerAmountRecognized == -20000 ) {
##         $EVoucher = "";
##      } else {
##         $EVoucher = sprintf("\$%0.2f", $dbOtherPayerAmountRecognized);
##      }
      
      my $dbDateOfServiceDisplay = substr($dbDateOfService, 4, 2) . "/" . substr($dbDateOfService, 6, 2) . "/" . substr($dbDateOfService, 0, 4);
      
      my $dbDateTransmittedDisplay = substr($dbDateTransmitted, 4, 2) . "/" . substr($dbDateTransmitted, 6, 2) . "/" . substr($dbDateTransmitted, 0, 4);
      
      $dbPSS_display = $nbsp;
      if ($dbPSS =~ /yes/i) {
        $dbPSS_display = qq#<img src="/images/time27.png" />#;
      }

      $dbCFA_display = $nbsp;
      if ($dbCFA =~ /yes/i) {
        $dbCFA_display = qq#<img src="/images/money146.png" />#;
      }
      
      if ($row % 2 == 0) {
        $row_color = "";
      } else {
        $row_color = "";
      }
      
      if ( $dbIntervention_ID == -20000 ) {
         $dbIntervention_ID = "";
      }
     
      print qq#
      <tr>
      <td class="$row_color">
        <input type="checkbox" name="selected_claims" class="checkboxes" value="$dbNCPDPNumber\#\#$dbRxNumber\#\#$dbDateOfService\#\#${dbTotalAmountPaid}\#\#${dbIntervention_ID}\#\#${incomingtbID}END">
      </td>
      <td class="$row_color">$dbNCPDPNumber</td>
      <td class="$row_color align_right">$dbRxNumber</td>
      <td class="$row_color">$dbDateOfServiceDisplay</td>
      <td class="$row_color">$dbDateTransmittedDisplay</td>
      <td class="$row_color align_right">\$$dbTotalAmountPaid</td>
      <td class="$row_color">$TCode</td>
<!--
      <td class="$row_color align_right">$EVoucher</td>
-->
      <td class="$row_color align_center">$dbPSS_display</td>
      <td class="$row_color align_center">$dbCFA_display</td>
      <td class="$row_color align_center"><a href="http://${WEBPREFIX}.paidesktop.com/cgi-bin/Interventions.cgi?inInterventionID=$dbIntervention_ID\#VU" target="_blank">$dbIntervention_ID</td>
      <td class="$row_color"><span class="status" title="Copy to text box" style="cursor: copy;">$dbStatus</span></td>
<!--
      <td class="$row_color align_center">$dbProcessorControlNumber</td>
-->
      </tr>\n#;
      
      $row++;
    }
    print qq#</tbody>\n#;
    print qq#</table>\n#;
    
    print qq#
    <INPUT TYPE="hidden" NAME="filter_in"   VALUE="$filter_in" >
    <INPUT TYPE="hidden" NAME="filter_ncpdp" VALUE="$filter_ncpdp" >
    <INPUT TYPE="hidden" NAME="daterange"    VALUE="$daterange" >
    <INPUT TYPE="hidden" NAME="datefrom"     VALUE="$datefrom" >
    <INPUT TYPE="hidden" NAME="dateto"       VALUE="$dateto" >
    <INPUT TYPE="hidden" NAME="filter_pss"   VALUE="$filter_pss" >
    <INPUT TYPE="hidden" NAME="filter_cfa"   VALUE="$filter_cfa" >
    <INPUT TYPE="hidden" NAME="show_ALU"     VALUE="$show_ALU" >
    #;
    
    print qq#<hr style="clear: both;" />#;
    
    print qq#
    <table width=100%>
    <tr><td width=50%>
    <span class="navy_text"><input type="checkbox" name="action" class="update_status action_options" value="status"> Update Status </span>
    </td><td width=50%>
    <span class="navy_text">
    <input type="checkbox" name="action" class="action_options mark"   value="mark pss"> Mark PSS <i>or</i>
    <input type="checkbox" name="action" class="action_options remove" value="remove pss"> Remove PSS  
    </span>
    </td></tr>
    <tr><td>
    <span class="navy_text"><input type="checkbox" name="action" class="add_intervention action_options" value="intervention"> Add Intervention </span>
    </td><td>
    <span class="navy_text">
    <input type="checkbox" name="action" class="action_options mark"   value="mark cfa"> Mark CFA <i>or</i>
    <input type="checkbox" name="action" class="action_options remove" value="remove cfa"> Remove CFA  
    </span>
    </td></tr>

    <tr><td width=50%>
    <span class="navy_text"><input type="checkbox" name="action" class="action_options" value="excel"> Export to Excel </span>
    </td><td>&nbsp</td>
    </td></tr>

    </table>
    <br />
    #;
    
    print qq#
    <textarea id="text_input_status" name="status_update" placeholder="Enter new status here, if applicable." maxlength=75 style="width: 550px;"></textarea><br />
    #;

    print qq#
    <textarea id="text_input_intervention" name="intervention_update" placeholder="Enter new intervention here, if applicable." style="width: 550px;"></textarea><br />
    #;
  
    print qq#</form>#;
  
    print qq#<p><button id="submit_form" class="button-form">Proceed with Action(s)</button></p>#;
  } else {
    print "<p>No rows found.</p>\n";
  }
  
  $sthx->finish;

}

#______________________________________________________________________________

sub readSelected {
  %selectedNCPDP    = ();
  %selectedRxNumber = ();
  %selectedDateOfService = ();
  %selectedTotalAmountPaid = ();
  %selectedInterventionID  = ();

  $rScount = 0;

  foreach $key (sort keys %in) {
    if ($key =~ /selected_claims/) {
      #print "<p>key: $key | value: $in{$key}</p>\n";
      my @selkeys = split('END', $in{$key});
      foreach (@selkeys) {
        my $key = $_;
        my @pcs = split('##', $key);
        $pcs[0] =~ s/\D//g;
        $selectedNCPDP{$key}           = $pcs[0];
        $selectedRxNumber{$key}        = $pcs[1];
        $selectedDateOfService{$key}   = $pcs[2];
        $selectedTotalAmountPaid{$key} = $pcs[3];
        $selectedInterventionID{$key}  = $pcs[4];
        $selectedID{$key}              = $pcs[5];
        #print "<p>read -- NCPDP: $pcs[0] | Rx#: $pcs[1] | DoS: $pcs[2] | Paid: $pcs[3]</p>\n";
        $rScount++;
      }
    } 
  } 
  return ($rScount);
}

#______________________________________________________________________________

sub processSelected {
  $claims_processed = 0;
  $buildWHERE = "";
  
  #Build WHERE statement
  foreach $key (sort keys %selectedRxNumber) {
    $thisNCPDP           = $selectedNCPDP{$key};
    $thisRxNumber        = $selectedRxNumber{$key};
    $thisDateOfService   = $selectedDateOfService{$key};
    $thisTotalAmountPaid = $selectedTotalAmountPaid{$key};
    $thisInterventionID  = $selectedInterventionID{$key};
    $thisID              = $selectedID{$key};
    
   ## print "<p>$thisID.....process -- NCPDP: $thisNCPDP | Rx#: $thisRxNumber | DoS: $thisDateOfService | Paid: $thisTotalAmountPaid</p>\n";
    
=cut
    $buildWHERE .= "(
       dbNCPDPNumber     = $thisNCPDP
    && dbRxNumber        = $thisRxNumber
    && dbDateOfService   = $thisDateOfService
    && dbTotalAmountPaid = $thisTotalAmountPaid
    && dbTotalAmountPaid > 0
    ) || ";
=cut
    $buildWHERE .= "(
       incomingtbID     = $thisID
    ) || ";
    
    $claims_processed++;
  }
  $buildWHERE =~ s/\|\|\s*$//;
  
  if ($action =~ /status/i && $status_update !~ /^\s*$/) {
    my $numrows = 0;
    
    foreach $table (@tables) {
      my $sql   = "
      UPDATE $USEDBNAME.$table 
      SET dbStatus = ?
      WHERE 
      ( 
      $buildWHERE 
      )
      ";

       ##  print "<hr> sql:<br><pre>$sql</pre><hr>\n";
    
      my $sthups = $dbx->prepare("$sql");
      $numrows = $sthups->execute($status_update);
      $sthups->finish;
    }
    
    if ($numrows !~ /0E0/ && $numrows > 0) {
      print "<p class=\"notification\"><strong>$claims_processed claim(s) have been updated with a status!</strong></p>\n";
    }
  }
  
  if ($action =~ /pss/i) {
    
    if ($action =~ /mark/i) {
      $setto = "'Yes'";
    } elsif ($action =~ /remove/i) {
      $setto = "NULL";
    } else {
      $setto = "NULL";
    }
    
    my $numrows = 0;
    
    foreach $table (@tables) {
      my $sql = "
      UPDATE $USEDBNAME.$table 
      SET dbPSS = $setto 
      WHERE 
      ( 
      $buildWHERE 
      )
      ";
    
      my $sthupss = $dbx->prepare("$sql");
      $numrows = $sthupss->execute;
      $sthupss->finish;
    }
    
    if ($numrows !~ /0E0/ && $numrows > 0) {
      print "<p class=\"notification\"><strong>$claims_processed claim(s) - Pending Success Story updated!</strong></p>\n";
    }
  }
   
  if ($action =~ /cfa/i) {
    if ($action =~ /mark/i) {
      $setto = "'Yes'";
    } elsif ($action =~ /remove/i) {
      $setto = "NULL";
    } else {
      $setto = "NULL";
    }
    
    my $numrows = 0;
    
    foreach $table (@tables) {
      my $sql = "
      UPDATE $USEDBNAME.$table 
      SET dbCFA = $setto 
      WHERE 
      ( 
      $buildWHERE 
      )
      ";
    
      my $sthucfa = $dbx->prepare("$sql");
      $numrows = $sthucfa->execute;
      $sthucfa->finish;
    }
    
    if ($numrows !~ /0E0/ && $numrows > 0) {
      print "<p class=\"notification\"><strong>$claims_processed claim(s) - Cash Flow Assistance updated!</strong></p>\n";
    }
  }

  if ($action =~ /intervention/i) {
     my $INTFOUND = 0;
     foreach $key (sort keys %selectedRxNumber) {
       my $thisNCPDP           = $selectedNCPDP{$key};
       my $thisRxNumber        = $selectedRxNumber{$key};
       my $thisDateOfService   = $selectedDateOfService{$key};
       my $thisTotalAmountPaid = $selectedTotalAmountPaid{$key};
       my $thisInterventionID  = $selectedInterventionID{$key};

       if ( $thisInterventionID !~ /^\s*$/ ) {
          $INTFOUND++;
          print "<p class=\"notification red\"><strong>No Interventions created! An Intervention already exists in the selection!<br>";
          print "NCPDP: $thisNCPDP, \n";
          print "RxNumber: $thisRxNumber, \n";
          print "Intervention ID: $thisInterventionID\n";
          print "</strong></p>\n";
       }
     }

     if ( !$INTFOUND ) {
        foreach $key (sort keys %selectedRxNumber) {
          my $thisNCPDP           = $selectedNCPDP{$key};
          my $thisRxNumber        = $selectedRxNumber{$key};
          my $thisDateOfService   = $selectedDateOfService{$key};
          my $thisTotalAmountPaid = $selectedTotalAmountPaid{$key};
          my $thisInterventionID  = $selectedInterventionID{$key};
   
          &buildIntervention($thisNCPDP);
   
        }
     }
  }

  if ($action =~ /excel/i) {
    &buildExcel;    
  }
}

#______________________________________________________________________________

sub buildExcel {
  my $sql = "SELECT dbBinNumber, dbNCPDPNumber, dbRxNumber, dbDateOfService, dbDateTransmitted, dbTotalAmountPaid, dbCode, dbProcessorControlNumber, dbGroupID, dbCardHolderID,
                    dbPatientFirstName, dbPatientLastName, dbDateOfBirth, dbStatus, dbPSS, dbCFA, dbIntervention_ID, dbOtherPayerAmountRecognized
               FROM $USEDBNAME.incomingtb 
               JOIN officedb.pharmacy ON dbNCPDPNumber = NCPDP
                 && Status_ReconRx = 'Active'
              WHERE ( 
                      $buildWHERE 
                    )
           ORDER BY dbNCPDPNumber, dbDateTransmitted";

  my $sthee = $dbx->prepare("$sql");
  my $numrows = $sthee->execute;
  
  if ($numrows !~ /0E0/ && $numrows > 0) {
    my $new_filter_in = $filter_in;        # don't overwrite the global filter_in variable
    if ( $filter_in =~ /->/ ) {
       my @pcs = split(/##|->/, $filter_in);
       $new_filter_in = "$pcs[0]##$pcs[1]##$pcs[$#pcs]";
    }

    my $save_location = "D:\\Recon-Rx\\Reports\\";
    my $filename = "Aging_Report_${new_filter_in}_${long_time}.xlsx";

    $filename =~ s/##/_/g;
    $filename =~ s/ /_/g;
    $filename =~ s/&/and/g;
    $filename =~ s/\(|\)//g;

    print qq#<p class="notification"><img src="/images/xlsx1.png" style="vertical-align: middle"><a href="/Reports/$filename">Download Spreadsheet (XLSX)</a></p>\n#;
    
    $workbook = Excel::Writer::XLSX->new( $save_location.$filename );
    $worksheet = $workbook->add_worksheet();
    $worksheet->set_landscape();
    $worksheet->fit_to_pages( 1, 0 ); #Fit all columns on a single page
    $worksheet->hide_gridlines(0); #0 = Show gridlines
    
    $worksheet->freeze_panes( 1, 0 ); #Freeze first row
    $worksheet->repeat_rows( 0 );    #Print on each page
    
    $worksheet->set_header("&LReconRx");
    
    $format_bold = $workbook->add_format();
    $format_bold->set_bold();
    
    $wrow = 1;
    $worksheet->write( "A$wrow", 'BIN', $format_bold); #0 
    $worksheet->write( "B$wrow", 'NCPDP', $format_bold);  #1
    $worksheet->write( "C$wrow", 'Rx', $format_bold); #2
    $worksheet->write( "D$wrow", 'Date of Service', $format_bold); #3
      $worksheet->set_column( 3, 3, 18 );
    $worksheet->write( "E$wrow", 'Processed Date', $format_bold); #4
      $worksheet->set_column( 4, 4, 18 );
    $worksheet->write( "F$wrow", 'Amount Due', $format_bold); #5
      $worksheet->set_column( 5, 5, 16 );
    $worksheet->write( "G$wrow", 'Code', $format_bold); #6
    $worksheet->write( "H$wrow", 'PCN', $format_bold); #7
      $worksheet->set_column( 7, 7, 18 );
    $worksheet->write( "I$wrow", 'Group', $format_bold); #8 
    $worksheet->write( "J$wrow", 'Cardhold ID', $format_bold); #9
      $worksheet->set_column( 9, 9, 18 );
    $worksheet->write( "K$wrow", 'Patient First Name', $format_bold); #10
      $worksheet->set_column( 10, 10, 18 );
    $worksheet->write( "L$wrow", 'Patient Last Name', $format_bold); #11
      $worksheet->set_column( 11, 11, 18 );
    $worksheet->write( "M$wrow", 'Patient DOB', $format_bold); #12
      $worksheet->set_column( 12, 12, 18 );
    $worksheet->write( "N$wrow", 'PSS', $format_bold); #13
    $worksheet->write( "O$wrow", 'CFA', $format_bold); #14
    $worksheet->write( "P$wrow", 'Int ID', $format_bold); #15
##    $worksheet->write( "Q$wrow", 'EVoucher', $format_bold); #16
    $worksheet->write( "R$wrow", 'Status', $format_bold); #17
      
    while ( my @row = $sthee->fetchrow_array() ) {
      my ($dbBinNumber, $dbNCPDPNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid, $dbCode, $dbProcessorControlNumber, $dbGroupID, $dbCardHolderID, $dbPatientFirstName, $dbPatientLastName, $dbDateOfBirth, $dbStatus, $dbPSS, $dbCFA, $dbIntervention_ID, $dbOtherPayerAmountRecognized ) = @row;
      
      my $dbDateOfServiceDisplay = substr($dbDateOfService, 4, 2) . "/" . substr($dbDateOfService, 6, 2) . "/" . substr($dbDateOfService, 0, 4);
      my $dbDateTransmittedDisplay = substr($dbDateTransmitted, 4, 2) . "/" . substr($dbDateTransmitted, 6, 2) . "/" . substr($dbDateTransmitted, 0, 4);
      my $dbDateOfBirthDisplay = substr($dbDateOfBirth, 4, 2) . "/" . substr($dbDateOfBirth, 6, 2) . "/" . substr($dbDateOfBirth, 0, 4);
=cut
      if ( $dbOtherPayerAmountRecognized == -20000 ) {
         $EVoucher = "";
      } else {
         $EVoucher = sprintf("%0.2f", $dbOtherPayerAmountRecognized);
      }
=cut
      
      my $format_left = $workbook->add_format();
      $format_left->set_align( 'left' );
      my $format_center = $workbook->add_format();
      $format_center->set_align( 'center' );
      my $format_right = $workbook->add_format();
      $format_right->set_align( 'right' );
      my $format_number = $workbook->add_format();
      $format_number->set_num_format( '#,##0' );
      my $format_money = $workbook->add_format();
      $format_money->set_num_format( '$#,##0.00' );
  
      $worksheet->keep_leading_zeros();
      
      #$worksheet->write( "A$wrow", $sumKEY, $format_left );  
  
      $wrow++;
  
      $worksheet->write( "A$wrow", $dbBinNumber );  
      $worksheet->write( "B$wrow", $dbNCPDPNumber );  
      $worksheet->write( "C$wrow", $dbRxNumber );  
      $worksheet->write( "D$wrow", $dbDateOfServiceDisplay );  
      $worksheet->write( "E$wrow", $dbDateTransmittedDisplay );  
      $worksheet->write( "F$wrow", $dbTotalAmountPaid );  
      $worksheet->write( "G$wrow", $dbCode );  
      $worksheet->write( "H$wrow", $dbProcessorControlNumber );  
      $worksheet->write( "I$wrow", $dbGroupID );  
      $worksheet->write( "J$wrow", $dbCardHolderID, $format_left );  
      $worksheet->write( "K$wrow", $dbPatientFirstName );  
      $worksheet->write( "L$wrow", $dbPatientLastName );  
      $worksheet->write( "M$wrow", $dbDateOfBirthDisplay );  
      $worksheet->write( "N$wrow", $dbPSS );
      $worksheet->write( "O$wrow", $dbCFA );
      $worksheet->write( "P$wrow", $dbIntervention_ID );
##      $worksheet->write( "Q$wrow", $EVoucher );
      $worksheet->write( "R$wrow", $dbStatus );  
      
    }
  
    $workbook->close(); #End XLSX
  }
  $sthee->finish;
}

#______________________________________________________________________________

sub getFilterNCPDPs {
  %filter_Pharmacy = ();
  %filter_NCPDPs  = ();
  %filter_PharmacyNames = ();

  my $DBNAME    = "officedb";
  my $TABLE     = "pharmacy";
  my $TABLE_coo = "pharmacy_coo";
  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name  
               FROM $DBNAME.$TABLE 
              WHERE Status_ReconRx = 'Active' 
                 && Type LIKE '%Recon%'
              UNION
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM $DBNAME.$TABLE_coo
              WHERE Status_ReconRx = 'Active' 
                 && Type LIKE '%Recon%'
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($Pharmacy_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    $filter_Pharmacy{$Pharmacy_ID}      = $NCPDP;
    $filter_NCPDPs{$Pharmacy_ID}        = $NCPDP;
    $filter_PharmacyNames{$Pharmacy_ID} = $Pharmacy_Name;
  }

  $sthx->finish;
}

#______________________________________________________________________________

sub buildIntervention {
  my ($thisNCPDP) = @_;

  my $DBNAME = "";
  if ( $testing ) {
     $DBNAME = "testing";
  } else {
     $DBNAME = "officedb";
  }

  my $user = $USER || $RUSER;
  my $sql = "";

  &readThirdPartyPayers;

#----------
# Set Type_ID in this section
  $Type_ID = $in_TPP_ID;

#----------
# Set CSR ID, CSR Name
  $sql = "SELECT WLSuperUser, WLLoginID, CONCAT(WLLastName, ', ', WLFirstName)
            FROM officedb.weblogintb
           WHERE WLLoginID = '$USER'";
  
  my $sthucfa = $dbx->prepare("$sql");
  $numrows = $sthucfa->execute;

  while ( my @row = $sthucfa->fetchrow_array() ) {
    ($WLSuperUser, $WLLoginID, $CSR_Name) = @row;    # do not "my" these as inside loop
  
   # Create Intervention. 
   # Find Intervention, set $setto = $Intervention_ID

   # INSERT INTO OfficeDB.Interventions
    $sql = "INSERT INTO $DBNAME.Interventions 
               SET Pharmacy_ID=$thisNCPDP,
                   Type = 'ThirdPartyPayer',
                   Type_ID = '$Type_ID',
                   Category = 'ReconRx - Aged Outstanding Prescriptions',
                   Program = 'ReconRx',
                   CSR_ID = '$WLSuperUser',
                   CSR_Name = '$CSR_Name',
                   Status = 'Active',
                   Opened_Date_TS = $opened_date_TS,
                   Opened_Date = '$opened_date',
                   Closed_Date_TS = NULL,
                   Closed_Date = NULL,
                   Comments = '\Q$intervention_update\E'";
   
    # see if we have already added an intervention for this already! If so, use it instead.
    if ( $SAVESQLS{"$sql"} ) {
       # we have already added an intervention for this already! Use it instead.
    } else {
       my $sthucfa = $dbx->prepare("$sql");
       $numrows = $sthucfa->execute;
       $sthucfa->finish;
       
       if ($numrows !~ /0E0/ && $numrows > 0) {
         print "<p class=\"notification\"><strong>Intervention created for NCPDP: $thisNCPDP</strong></p>\n";
       }
       $sthucfa->finish;
     }
  }
  $SAVESQLS{"$sql"}++;

#------
# Now find what Intervention_ID was created
  $sql = qq#
SELECT Intervention_ID 
FROM $DBNAME.Interventions
WHERE 1=1
&& Pharmacy_ID=$thisNCPDP
&& Type="ThirdPartyPayer"
&& Type_ID="$Type_ID"
&& Category="ReconRx - Aged Outstanding Prescriptions"
&& Program="ReconRx"
&& CSR_ID="$WLSuperUser"
&& CSR_Name="$CSR_Name"
&& Status="Active"
&& Opened_Date_TS=$opened_date_TS
&& Opened_Date="$opened_date"
&& Closed_Date_TS IS NULL
&& Closed_Date IS NULL
&& Comments="\Q$intervention_update\E"
#;

  my $sthucfa = $dbx->prepare("$sql");
  $numrows = $sthucfa->execute;
  
  while ( my @row = $sthucfa->fetchrow_array() ) {
    ($Intervention_ID) = @row;
  }
  if ($numrows !~ /0E0/ && $numrows > 0) {
  }
  $sthucfa->finish;

  $setto = $Intervention_ID;
#------
    
  my $numrows = 0;

  foreach $table (@tables) {
    my $sql = qq#
UPDATE $USEDBNAME.$table 
SET dbIntervention_ID = $setto 
WHERE (1=1)
&& dbNCPDPNumber = $thisNCPDP
&&
( 
$buildWHERE 
)
    #;
  
    my $sthucfa = $dbx->prepare("$sql");
    $numrows = $sthucfa->execute;
    $sthucfa->finish;
  }
}

#______________________________________________________________________________

sub buildALU {
 
# Auto Look Up
# ADD Auto-Look-Up (in box, somewhere on the Aging Dashboard Tool screen).
# This will allow ReconRx staff to identify Interventions associated with Rx’s that have now been paid.
# Use the following criteria:

#   Third Party Payer   = <<Payer Select on Dashboard Tool>>
#   Category            = ReconRx - Aged Outstanding Prescriptions
#   Intervention Status = Open
#   Intervention ID - not listed on active Dashboard Aging Tool as associated with an open claim.

# Display these Intervention ID’s (make "clickable") so ReconRx staff can be redirected
# to the Intervention Update/Close page (as seen above).

  my $DBNAME = "";
  if ( $testing ) {
     $DBNAME = "testing";
  } else {
     $DBNAME = "officedb";
  }

  &readPharmacies;
  &readThirdPartyPayers;

#----------
# Set Type_ID in this section
  $Type_ID1 = $Reverse_TPP_BINs{$filter_in};
  $Type_ID2 = $Reverse_TPP_BINs2{$filter_in};
  $Type_ID3 = $Reverse_TPP_BINs_ALL{$filter_in};

print "Type_ID1 : $Type_ID1<br>\n";
print "Type_ID2 : $Type_ID2<br>\n";
print "Type_ID3 : $Type_ID3<br>\n";
print "in_TPP_ID: $in_TPP_ID<br>\n";

  $Type_ID = $Type_ID1 || $Type_ID2 || $Type_ID3 || "000000";

  print "<hr size=8 color=green>\n";
  print "<h2>Auto-Look-Up for Payer: $TPP_Names{$Type_ID}</h2>\n";
  

#------
  $SAVEINTS =~ s/,\s*$//;
# Now find the Auto-Look-Up entries
  $sql = qq#
SELECT Pharmacy_ID, Intervention_ID 
FROM $DBNAME.Interventions
WHERE 1=1
&& Type="ThirdPartyPayer"
&& Type_ID="$Type_ID"
&& Category="ReconRx - Aged Outstanding Prescriptions"
&& Program="ReconRx"
&& Status="Active"
#;
  $sql .= qq# && Intervention_ID NOT IN ($SAVEINTS) # if ( $SAVEINTS !~ /^\s*$/ );
  $sql .= qq# ORDER BY Pharmacy_ID, Intervention_ID #;

  my $sthucfa = $dbx->prepare("$sql");
  $numrows = $sthucfa->execute;

  print qq#<table>\n#;
  print qq#<tr><th>Intervention ID</th><th>NCPDP</th><th>Pharmacy Name</th></tr>\n#;

  while ( my @row = $sthucfa->fetchrow_array() ) {
    ($Pharmacy_ID, $Intervention_ID) = @row;
    my $Pharmacy_Name = $Pharmacy_Names{$Pharmacy_ID};
    print qq#<tr>\n#;
    print qq#<td align=center><a href="http://${WEBPREFIX}.paidesktop.com/cgi-bin/Interventions.cgi?inInterventionID=$Intervention_ID\#VU" target="_blank">$Intervention_ID</td>\n#;
    print qq#<td>$Pharmacy_ID</td>\n#;
    print qq#<td>$Pharmacy_Name</td>\n#;
    print qq#</tr>\n#;
  }

  print qq#</table>\n#;

  $sthucfa->finish;
  print "<hr size=8 color=green>\n";
}

#______________________________________________________________________________
