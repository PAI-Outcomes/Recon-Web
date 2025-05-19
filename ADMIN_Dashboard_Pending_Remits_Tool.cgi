use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;  

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
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

if ( $ReconRx_Admin_Dashboard_Pending_Remits_Tool !~ /^Yes/i ) {
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
print qq#<strong>$Title</strong><br>\n#;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;    # reported as "years since 1900".
$month += 1;    # reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

$long_time  = sprintf("%04d%02d%02d%02d%02d", $year, $month, $day, $hour, $min);

($in_TPP_ID, $in_TPP_BIN, $in_TPP_NAME) = split("##", $filter_in, 3);
 
#______________________________________________________________________________
#______________________________________________________________________________

#####$testing++;

if ( $testing ) {
 
   $JJJ = $DBNAMES{"R8DBNAME"}; print "JJJ: $JJJ<br>\n";
  
   $WHICHDB = "Testing";        # Valid Values: "Testing" or "Webinar"
   &set_Webinar_or_Testing_DBNames;
  
   $HHH = $DBNAMES{"R8DBNAME"}; print "HHH: $HHH<br>\n";

   print "R8DBNAME: $R8DBNAME, R8TABLE : $R8TABLE<br>\n";
   print "P8DBNAME: $P8DBNAME, P8TABLE : $P8TABLE<br>\n";
   print "<hr>\n";
   $USEDBNAME = "testing";
} else {
   $USEDBNAME = "reconrxdb";
}

#______________________________________________________________________________
#______________________________________________________________________________

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&readSelected;
&processSelected;

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
      \$('\#text_input').html(edit);
    });
    
  });
  
  function checkData1() {
    if ( \$('\#daterange_range').is(':checked') && (\$('\#datefrom_value').val() == '' || \$('\#dateto_value').val() == '') ) {
      alert('If using "Range", you must set both dates!');
      return false;
    }
  }

  function checkData2() {
    if ( \$('.checkboxes').is(':checked') && \$('.action_options').is(':checked')) {
      //great
    }else{
      alert('Select at least one claim and choose an action.');
      return false;
    }
    if ( \$('.update_status').is(':checked') && \$('\#text_input').val() === '') {
      alert('No status has been entered to update!');
      return false;
    }
  }
  
  </script>
  #;
  
  print qq#<form action="$PROG" method="post" onsubmit="return checkData1()">#;
  
  # -------------------------------------------------------------------------------- #
  
  ($filterPCN) = &getFilterPayers($in_TPP_ID,$in_TPP_BIN,$in_TPP_NAME);

  print "in_TPP_ID: $in_TPP_ID<br>\n" if ($debug);

  my ($TPP_ID, $TPP_BIN, $TPP_NAME);
  if ($filter_in !~ /^\s*$/) {
    $TPP_NAME = "";
    foreach $key (sort { $filter_PayerNames{$a} cmp $filter_PayerNames{$b} } keys %filter_PayerNames) {
      ($TPP_ID, $TPP_BIN, $TPP_NAME) = split("##", $key, 3);
#     print "key: $key<br>\n";
#     print "check against: key =~ /^${in_TPP_ID}##${in_TPP_BIN}##/ <br>\n";
      if ( $key =~ /^${in_TPP_ID}##${in_TPP_BIN}##/ ) {
        $TPP_NAME = $filter_PayerNames{$key};
        last;
      }
    }
    $defalt_bin    = $filter_in;
    $default_payer = "${TPP_ID} - ${TPP_BIN} - ${TPP_NAME}";
  } else {
    $defalt_bin    = "";
    $default_payer = "Select a Payer";
  }

  print qq#<p><select name="filter_in" class="recon-dropdown-form">\n#;
  print qq#<option value="$defalt_bin">$default_payer</option>\n#;

  foreach $key (sort { $filter_PayerNames{$a} cmp $filter_PayerNames{$b} } keys %filter_PayerNames) {
    my $TPP_ID   = $filter_PayerIDs{$key};
    my $TPP_BIN  = $filter_PayerBINs{$key};
    my $TPP_NAME = $filter_PayerNames{$key};
    my $value = "${TPP_ID}##${TPP_BIN}##${TPP_NAME}";
    print qq#<option value="$value">$TPP_ID - $TPP_BIN - $TPP_NAME</option>\n#;
  }

  print qq#</select></p>#;
  # -------------------------------------------------------------------------------- #
  
  # -------------------------------------------------------------------------------- #
  &getFilterNCPDPs();
  print qq#<p><select name="filter_ncpdp" class="recon-dropdown-form">\n#;
  if ($filter_ncpdp !~ /^\s*$/) {
    $selected_ncpdp    = $filter_ncpdp;
    $selected_name = "$filter_ncpdp - " . $filter_PharmacyNames{$filter_ncpdp};
    print qq#<option value="$selected_ncpdp">$selected_name</option>\n#;
  } 
  print qq#<option value="">All Pharmacies</option>\n#;
  foreach $key (sort { $filter_PharmacyNames{$a} cmp $filter_PharmacyNames{$b} } keys %filter_PharmacyNames) {
    my $NCPDP  = $filter_NCPDPs{$key};
    my $NAME   = $filter_PharmacyNames{$key};
    print qq#<option value="$key">$NCPDP - $NAME</option>\n#;
  }
  print qq#</select></p>#;
  # -------------------------------------------------------------------------------- #
  
  $CHECKED_all   = '';
  $CHECKED_range = '';
  $CHECKED_pss   = '';
  
  if ($daterange =~ /all/i) {
    $CHECKED_all   = 'CHECKED';
  } elsif ($daterange =~ /range/i) {
    $CHECKED_range = 'CHECKED';
  } else {
    $CHECKED_all   = 'CHECKED';
  }
  
  if ($filter_pss =~ /yes/i) {
    $CHECKED_pss   = 'CHECKED';
  }
  
  if ($filter_ach =~ /yes/i) {
    $CHECKED_ach   = 'CHECKED';
  }
  
  print qq#<p>
  <input type="radio" name="daterange" id="daterange_all"   value="All" $CHECKED_all> All &nbsp; <i>or</i> 
  <input type="radio" name="daterange" id="daterange_range" value="Range" $CHECKED_range> Date Range 
  &nbsp; &nbsp; &nbsp; 
  <input type="checkbox" name="filter_pss" value="Yes" $CHECKED_pss>Show Only Checks Marked PSS
  &nbsp; &nbsp; &nbsp;
  <input type="checkbox" name="filter_ach" value="Yes" $CHECKED_ach>DO NOT SHOW ACH payments
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
      &nbsp; 
      To: <INPUT class="datepicker" TYPE="text" NAME="dateto" id="dateto_value" VALUE="$datetoDisplay" >
      &nbsp; (Date of Service)
    </p>
  </div>
  #;
  
  print qq#<p><INPUT class="button-form" TYPE="submit" VALUE="Find Pending Remits"></p>#;
  print qq#</form>#;
  
  print "<hr />\n";
  
  if ($filter_in !~ /^\s*$/) {
    &displayDataWeb();
  } else {
    print "<p>You must at least select a payer to continue</p>";
  }
}

#______________________________________________________________________________

sub displayDataWeb {

  #%filter_PayerIDs   = ();

  my $dbin    = "R8DBNAME";
  my $DBNAME  = $DBNAMES{"$dbin"};
  my $TABLE   = 'Checks';

  my $sql = "SELECT R_TS3_NCPDP, R_TPP, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_BPR16_Date, R_BPR04_Payment_Method_Code, R_Status, R_PSS
               FROM $DBNAME.$TABLE 
          LEFT JOIN officedb.third_party_payers tpp
                 ON R_TPP_PRI = Third_Party_Payer_ID
              WHERE R_PENDRECV = 'P' 
                 && R_BPR02_Check_Amount > 0";
  
  if ($filter_in !~ /^\s*$/ && $filter_in > 0) {
#   $sql .= "&& tpp.BIN = $filter_in\n";
    $sql .= "&& tpp.BIN = $in_TPP_BIN\n";
    $sql .= "&& tpp.Third_Party_Payer_ID = $in_TPP_ID\n";
  }
  
  if ($filter_ncpdp !~ /^\s*$/ && $filter_ncpdp > 0) {
    $sql .= "&& $TABLE.Pharmacy_ID = $filter_ncpdp\n";
  }
  
  if ($datefrom !~ /^\s*$/ && $dateto !~ /^\s*$/ && $daterange =~ /range/i) {
    if ($datefrom =~ /\//) {
      my @pcs = split('/', $datefrom);    
      $datefrom = sprintf("%04d%02d%02d", $pcs[2], $pcs[0], $pcs[1]);
      @pcs = split('/', $dateto);    
      $dateto = sprintf("%04d%02d%02d", $pcs[2], $pcs[0], $pcs[1]);
    }
    $sql .= "&& R_BPR16_Date >= $datefrom && R_BPR16_Date <= $dateto\n";
  } 
  
  if ($filter_pss !~ /^\s*$/) {
    $sql .= "&& (R_PSS != '' && R_PSS IS NOT NULL)\n";
  }
  
  if ($filter_ach !~ /^\s*$/) {
    #Payer specific exceptions should now be taking place in the PUT IN DB process, however to support ancient remits this query still contains some of them.
    $sql .= "&& (R_BPR04_Payment_Method_Code != 'ACH' && R_BPR04_Payment_Method_Code != 'FWT') 
             && R_TPP_PRI != 700165 #Script Care
             && R_TPP_PRI != 700126 #NPS
             && R_TPP_PRI != 700172 #Tx Med
             && ( (R_TPP_PRI = 700002 && (TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE '7%' && TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE '800%') ) || (R_TPP_PRI != 700002) ) #Caremark
             && ( (R_TPP_PRI = 700186 && TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE 'FACH%') || (R_TPP_PRI != 700186) ) #RxOptions
             && ( (R_TPP_PRI = 700120 && TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE '3%') || (R_TPP_PRI != 700120) ) #MedImpact
             && ( (R_TPP_PRI = 700173 && TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE '400%' && TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE '500%' && TRIM(LEADING '0' FROM R_TRN02_Check_Number) NOT LIKE '800%') || (R_TPP_PRI != 700173) ) #Tmesys";
  }
  
  $sql .= "GROUP BY R_TS3_NCPDP, R_TRN02_Check_Number
           ORDER BY R_TS3_NCPDP, R_BPR16_Date";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;

  my $sthx  = $dbx->prepare("$sql");
  my $numrows = $sthx->execute;
  
  if ($numrows > 0) {
    #print "<p>The following claims are over 45 days old and have no potential remit matches.</p>\n";
    print qq#<form action="$PROG" method="post" onsubmit="return checkData2()">#;
    print qq#<table class="main">\n#;
    print qq#
    <tr>
    <th><input type="checkbox" name="selectall" id="selectallboxes" value=""></th>
    <th>NCPDP</th>
    <th>TPP</th>
    <th>Check\#</th>
    <th>Check Amount</th>
    <th>Check Date</th>
    <th>Pmt Type</th>
    <th>PSS</th>
    <th>Status</th>
    </tr>\n#;
    
    my $row = 1;
    
    while ( my @row = $sthx->fetchrow_array() ) {
      my ($R_TS3_NCPDP, $R_TPP, $R_TRN02_Check_Number, $R_BPR02_Check_Amount, $R_BPR16_Date, $R_BPR04_Payment_Method_Code, $R_Status, $R_PSS ) = @row;
      
      $R_TS3_NCPDP = sprintf("%07d", $R_TS3_NCPDP);
      
      my $R_BPR16_DateDisplay = substr($R_BPR16_Date, 4, 2) . "/" . substr($R_BPR16_Date, 6, 2) . "/" . substr($R_BPR16_Date, 0, 4);
      
      $R_PSS_display = '';
      if ($R_PSS =~ /yes/i) {
        $R_PSS_display = qq#<img src="/images/time27.png" />#;
      }
      
      if ($row % 2 == 0) {
        $row_color = "lj_blue_table";
      } else {
        $row_color = "";
      }
      
      print qq#
      <tr>
      <td class="$row_color">
        <input type="checkbox" name="selected_checks" class="checkboxes" value="$R_TS3_NCPDP\#\#$R_TRN02_Check_Number\#\#$R_BPR16_Date\#\#${R_BPR02_Check_Amount}END">
      </td>
      <td class="$row_color">$R_TS3_NCPDP</td>
      <td class="$row_color">$R_TPP</td>
      <td class="$row_color">$R_TRN02_Check_Number</td>
      <td class="$row_color" align=right>$R_BPR02_Check_Amount</td>
      <td class="$row_color">$R_BPR16_DateDisplay</td>
      <td class="$row_color">$R_BPR04_Payment_Method_Code</td>
      <td class="$row_color align_center">$R_PSS_display</td>
      <td class="$row_color"><span class="status" title="Copy to text box" style="cursor: copy;">$R_Status</span></td>
      </tr>\n#;
      
      $row++;
    }
    print "</table>\n";
    
    print qq#
    <INPUT TYPE="hidden" NAME="filter_in" VALUE="$filter_in" >
    <INPUT TYPE="hidden" NAME="filter_ncpdp" VALUE="$filter_ncpdp" >
    <INPUT TYPE="hidden" NAME="daterange" VALUE="$daterange" >
    <INPUT TYPE="hidden" NAME="datefrom" VALUE="$datefrom" >
    <INPUT TYPE="hidden" NAME="dateto" VALUE="$dateto" >
    <INPUT TYPE="hidden" NAME="filter_pss" VALUE="$filter_pss" > 
    <INPUT TYPE="hidden" NAME="filter_ach" VALUE="$filter_ach" >
    #;
    
    print qq#<hr />#;
    
    print qq#
    <span class="notification white"><input type="checkbox" name="action" class="update_status action_options" value="status"> Update Status </span>
    <span class="notification white">
      <input type="checkbox" name="action" class="action_options mark" value="mark pss"> Mark PSS <i>or</i>
      <input type="checkbox" name="action" class="action_options remove" value="remove pss"> Remove PSS  
    </span>
    <span class="notification white"><input type="checkbox" name="action" class="action_options" value="excel"> Export to Excel </span><br /><br />
    #;
    
    print qq#
    <textarea id="text_input" name="status_update" placeholder="Enter new status here, if applicable." maxlength=75 style="width: 550px;"></textarea><br />
    #;
    
    print qq#<p><INPUT class="button-form" TYPE="submit" VALUE="Proceed with Action(s)"></p>#;
    print qq#</form>#;
  } else {
    print "<p>No rows found.</p>\n";
  }
  
  $sthx->finish;
}

#______________________________________________________________________________

sub readSelected {
  %selectedNCPDP    = ();
  %selectedCheckNumber = ();
  %selectedCheckDate = ();
  %selectedCheckAmount = ();

  foreach $key (sort keys %in) {
    if ($key =~ /selected_checks/) {
      #print "<p>key: $key | value: $in{$key}</p>\n";
      my @selkeys = split('END', $in{$key});
      foreach (@selkeys) {
        my $key = $_;
        my @pcs = split('##', $key);
        $pcs[0] =~ s/\D//g;
        $selectedNCPDP{$key} = $pcs[0];
        $selectedCheckNumber{$key} = $pcs[1];
        $selectedCheckDate{$key} = $pcs[2];
        $selectedCheckAmount{$key} = $pcs[3];
      }
    } 
  } 
}

#______________________________________________________________________________

sub processSelected {
  $checks_processed = 0;
  $buildWHERE = '';
  
  my $table = "Checks";
  
  #Build WHERE statement
  foreach $key (sort keys %selectedCheckNumber) {
    my $thisNCPDP = $selectedNCPDP{$key};
    my $thisCheckNumber = $selectedCheckNumber{$key};
    my $thisCheckDate = $selectedCheckDate{$key};
    my $thisCheckAmount = $selectedCheckAmount{$key};
    
    $buildWHERE .= "(
       R_TS3_NCPDP = $thisNCPDP 
    && R_TRN02_Check_Number = '$thisCheckNumber'
    && R_BPR16_Date = $thisCheckDate
    && R_BPR02_Check_Amount = $thisCheckAmount
    ) || 
    ";
    
    $checks_processed++;
  }
# substr($buildWHERE, -5) = '';
  $buildWHERE =~ s/ \|\|\s*$//g;
  
  if ($action =~ /status/i && $status_update !~ /^\s*$/) {
    my $numrows = 0;
    
    #foreach (@tables) {
      #my $table = $_;
      my $sql = "
      UPDATE $DBNAME.$table 
      SET R_Status = '$status_update'
      WHERE ( 
      $buildWHERE 
      )
      ";

      ($sqlout = $sql) =~ s/\n/<br>\n/g;
      print "<p>UPDATE R_Status sql<br>\n$sqlout<br>status_update: $status_update<hr>\n" if ($debug);
    
#####
    if ($OWNER !~ /^\s*$/) { $POSTER = $OWNER; } else { $POSTER = $Pharmacy_Name; }
    &logActivity($POSTER, $sql, $USER);
#####

      my $sthups = $dbx->prepare("$sql");

#     $numrows = $sthups->execute($status_update);
      $numrows = $sthups->execute;

      $sthups->finish;
    #}
    
    if ($numrows !~ /0E0/ && $numrows > 0) {
      print "<p class=\"notification\"><strong>$checks_processed check(s) have been updated with a status!</strong></p>\n"
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
    
    #foreach (@tables) {
      #my $table = $_;
      my $sql = "
      UPDATE $DBNAME.$table 
      SET R_PSS = $setto 
      WHERE 
      ( 
      $buildWHERE 
      )
      ";
      ($sqlout = $sql) =~ s/\n/<br>\n/g;
      print "<p>UPDATE R_PSS sql<br>\n$sqlout<br>setto: $setto<hr>\n" if ($debug);
    
#####
      if ($OWNER !~ /^\s*$/) { $POSTER = $OWNER; } else { $POSTER = $Pharmacy_Name; }
      &logActivity($POSTER, $sql, $USER);
#####
      my $sthupss = $dbx->prepare("$sql");
      $numrows = $sthupss->execute;
      $sthupss->finish;
    #}
    
    if ($numrows !~ /0E0/ && $numrows > 0) {
      print "<p class=\"notification\"><strong>$checks_processed check(s) - Pending Success Story updated!</strong></p>\n"
    }
    
  }
  
  if ($action =~ /excel/i) {
    &buildExcel;    
  }
}

#______________________________________________________________________________

sub buildExcel {
  my $table = "Checks";

  my $sql = "
    SELECT R_TPP, R_TS3_NCPDP, R_TRN02_Check_Number, R_BPR16_Date, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, R_CheckReceived_Date, R_Status, R_PSS 
    FROM $DBNAME.$table 
    WHERE 
    ( 
    $buildWHERE 
    )
    GROUP BY R_TS3_NCPDP, R_TRN02_Check_Number
    ORDER BY R_TS3_NCPDP, R_BPR16_Date
  ";
    ($sqlout = $sql) =~ s/\n/<br>\n/g;
    print "<p>SELECT sql<br>\n$sqlout<br><hr>\n" if ($debug);
  
  my $sthee = $dbx->prepare("$sql");
  my $numrows = $sthee->execute;
  
  if ($numrows !~ /0E0/ && $numrows > 0) {
  
    my $save_location = "D:\\Recon-Rx\\Reports\\";
    my $filename = "Pending_Remits_Report_${filter_in}_${long_time}.xlsx";
    $filename =~ s/##/_/g;
    $filename =~ s/ //g;
    print "save_location: $save_location<br>filename: $filename<br>\n" if ($debug);
    
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
    $worksheet->write( "A$wrow", 'TPP', $format_bold); #0 
      $worksheet->set_column( 0, 0, 18 );
    $worksheet->write( "B$wrow", 'NCPDP', $format_bold);  #1
    $worksheet->write( "C$wrow", 'Check#', $format_bold); #2
      $worksheet->set_column( 2, 2, 18 );
    $worksheet->write( "D$wrow", 'Check Date', $format_bold); #3
      $worksheet->set_column( 3, 3, 18 );
    $worksheet->write( "E$wrow", 'Payment Type', $format_bold); #4
      $worksheet->set_column( 4, 4, 15 );
    $worksheet->write( "F$wrow", 'Check Amount', $format_bold); #5
      $worksheet->set_column( 5, 5, 15 );
    $worksheet->write( "G$wrow", 'Check Received Date', $format_bold); #6
      $worksheet->set_column( 6, 6, 18 );
    $worksheet->write( "H$wrow", 'PSS', $format_bold); #7
    $worksheet->write( "I$wrow", 'Status', $format_bold); #8 
      
      while ( my @row = $sthee->fetchrow_array() ) {
      my ($R_TPP, $R_TS3_NCPDP, $R_TRN02_Check_Number, $R_BPR16_Date, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount, $R_CheckReceived_Date, $R_Status, $R_PSS ) = @row;
      
      my $R_BPR16_DateDisplay = substr($R_BPR16_Date, 4, 2) . "/" . substr($R_BPR16_Date, 6, 2) . "/" . substr($R_BPR16_Date, 0, 4);
      $R_CheckReceived_Date =~ s/-//g;
      my $R_CheckReceived_DateDisplay = substr($R_CheckReceived_Date, 4, 2) . "/" . substr($R_CheckReceived_Date, 6, 2) . "/" . substr($R_CheckReceived_Date, 0, 4);
      
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
  
      $worksheet->write( "A$wrow", $R_TPP );  
      $worksheet->write( "B$wrow", $R_TS3_NCPDP );  
      $worksheet->write( "C$wrow", $R_TRN02_Check_Number );  
      $worksheet->write( "D$wrow", $R_BPR16_DateDisplay );  
      $worksheet->write( "E$wrow", $R_BPR04_Payment_Method_Code );  
      $worksheet->write( "F$wrow", $R_BPR02_Check_Amount ); 
      $worksheet->write( "G$wrow", $R_CheckReceived_DateDisplay );  
      $worksheet->write( "H$wrow", $R_PSS );  
      $worksheet->write( "I$wrow", $R_Status );  
      
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

# && Status = 'Active'

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";
  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name  
               FROM $DBNAME.$TABLE 
              WHERE Status_ReconRx = 'Active' 
                 && Type LIKE '%Recon%' 
           ORDER BY Pharmacy_Name";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($Pharmacy_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    $filter_Pharmacy{$Pharmacy_ID}      = $Pharmacy_ID;
    $filter_NCPDPs{$Pharmacy_ID}        = $NCPDP;
    $filter_PharmacyNames{$Pharmacy_ID} = $Pharmacy_Name;
  }
  $sthx->finish;
}

#______________________________________________________________________________
#______________________________________________________________________________
