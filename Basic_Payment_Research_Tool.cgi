use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use Excel::Writer::XLSX;  

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $tpp_ids = ();
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
my $emtemplate; 
my $filename;
my $zfilename;
my $save_location; 
my $Pharmacy_NCPDP;
$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

foreach $key (sort keys %in) {
  $$key = $in{$key};
}

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} else {
##   &ReconRxGotoNewLogin;
##   &MyReconRxTrailer;
   exit(0);
}

#______________________________________________________________________________

$ReconRx_Admin_Dashboard_Pending_Remits_Tool = 'Yes';

if ( $ReconRx_Admin_Dashboard_Pending_Remits_Tool !~ /^Yes/i ) {
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

($Title = $prog) =~ s/_/ /g;
 $Title =~ s/AreteRx/Arete Pharmacy Network/;

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

($in_TPP_ID, $in_TPP_BIN, $in_TPP_NAME) = split("-", $filter_in, 3);
 
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

my $DBNAME  = 'reconrxdb';
my $TABLE   = 'checks';

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

&displayTPP;
&readThirdPartyPayers;
&readSelected;
&processSelected;

&displayPage;
$dbx->disconnect;

##&MyReconRxTrailer;

exit(0);

 
  ##print qq#<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
  ##<script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
  ##<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />
sub displayPage {
  print "<hr>\n";
  
  print qq#
    <script src="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.6/js/standalone/selectize.min.js" integrity="sha256-+C0A5Ilqmu4QcSPxrlGpaZxJ04VjsRjKu+G82kl5UJk=" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/selectize.js/0.12.6/css/selectize.bootstrap3.min.css" integrity="sha256-ze/OEYGcFbPRmvCnrSeKbRTtjG4vGLHXgOqsyLFTRjg=" crossorigin="anonymous" />
  #;
  
  print qq#
  <script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>
  <script>
  
  //Execute the following only after the page has fully loaded.
    \$(document).ready(function () {
      \$('select').selectize({
          sortField: 'text'
      });
  });
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

   \$('\#tpp_id').change(function() {
        var x = \$(this).val();
        \$('\#filter_in').val(x);
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
  function etemplate(p,t) {
  var myWindow = window.open("", "MsgWindow", "width=600,height=300");
  myWindow.document.write("<p>RE:" + t +",</p>");
  myWindow.document.write("<p>" + p);
  myWindow.document.write(" does not have record of receiving the attached payments. Please research the attached payments " + 
  "and let me know if your records indicate they have been cashed. If so, please provide a copy of the cleared checks. " +
  "In the event the checks are outstanding, please reissue the checks and provide the reissued check information (check number, date, amount) " +
  "when available. Furthermore, please provide the date in which we can expect to receive the reissued amount. </p> ");
  myWindow.document.write("<p>Thank you,</p>");
  }

  
  </script>
  #;
  
  print qq#<form action="$PROG" method="post" >#;
  
  # -------------------------------------------------------------------------------- #
  
  print "in_TPP_ID: $in_TPP_ID<br>\n" if ($debug);

  my ($TPP_ID, $TPP_BIN, $TPP_NAME);
  if ($filter_in !~ /^\s*$/) {
    $defalt_bin    = $filter_in;
    $default_payer = "${TPP_ID} - ${TPP_BIN} - ${TPP_NAME}";
  } else {
    $defalt_bin    = "";
    $default_payer = "Select a Payer";
  }

  print qq# <table class='noborders'><tr>
    <select id="tpp_id" placeholder="Third Party Payer..." value="$filter_in" >#;
      print qq#<option value="">Select a payer</option>\n#;
    foreach $key (sort { $tpp_ids{$a} cmp $tpp_ids{$b} } keys %tpp_ids) {
      my $TPP_ID   = $key;
      my $TPP_BIN  = $TPP_BINs{$key};
      my $TPP_NAME = $TPP_Names{$key};
      $select = '';
      $select = 'selected' if("$TPP_ID - $TPP_BIN - $TPP_NAME" eq "$filter_in");
      print qq#<option $select value="$TPP_ID - $TPP_BIN - $TPP_NAME">$TPP_NAME </option>\n#;
    }
  print qq# </select></td>#;
 
  print qq#</td></tr></div></table>#;
  
  print qq#<INPUT TYPE="hidden" ID="filter_in" NAME="filter_in">#;
  print qq#<br><br><br><p><INPUT class="button-form" TYPE="submit" VALUE="Find Pending Remits"></p>#;
  print qq#</form>#;
  
  print "<hr />\n";
  
  if ($filter_in !~ /^\s*$/) {
    &displayDataWeb();
  } else {
    print "<p>You must at least select a payer to continue</p>";
  }
}

sub displayTPP {
  my $DBName = 'reconrxdb'; 
  $DBName = 'webinar' if ($PH_ID == 23); 

  my $sql = "SELECT R_TPP_PRI FROM $DBName.835remitstb a
              WHERE pharmacy_id = $PH_ID 
              UNION
             SELECT R_TPP_PRI FROM $DBName.835remitstb_archive a
              WHERE pharmacy_id = $PH_ID 
            ";

  my $sthx  = $dbx->prepare("$sql");
  my $numrows = $sthx->execute;

  while ( my $id = $sthx->fetchrow() ) {
    $tpp_ids{$id} = 1;
  }
}

sub displayDataWeb {

  #%filter_PayerIDs   = ();

  $DBNAME = 'webinar' if ($PH_ID == 23); 

  my $sql = "SELECT R_TS3_NCPDP, R_TPP, R_TRN02_Check_Number, R_BPR02_Check_Amount, R_BPR16_Date, R_BPR04_Payment_Method_Code
               FROM $DBNAME.$TABLE 
          LEFT JOIN officedb.third_party_payers tpp
                 ON R_TPP_PRI = Third_Party_Payer_ID
              WHERE R_PENDRECV = 'P' 
                 && R_BPR02_Check_Amount > 0";
  
  if ($filter_in !~ /^\s*$/ && $filter_in > 0) {
    $sql .= "&& tpp.BIN = $in_TPP_BIN\n";
    $sql .= "&& tpp.Third_Party_Payer_ID = $in_TPP_ID\n";
  }
  
  $sql .= "&& $TABLE.Pharmacy_ID = $PH_ID\n";
  
  $sql .= "GROUP BY R_TS3_NCPDP, R_TRN02_Check_Number
           ORDER BY R_TS3_NCPDP, R_BPR16_Date";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  my $sthx  = $dbx->prepare("$sql");
  my $numrows = $sthx->execute;
  
  if ($numrows > 0) {
    print qq#<form action="$PROG" method="post" onsubmit="return checkData2()">#;
    print qq#<table class="main">\n#;
    print qq#
    <tr>
    <th><input type="checkbox" name="selectall" id="selectallboxes" value=""></th>
    <th>NCPDP</th>
    <th>TPP</th>
    <th>Check\#</th>
    <th width='100px'style="padding-right:20px">Check Amount</th>
    <th>Check Date</th>
    <th>Pmt Type</th>
    </tr>\n#;
    
    my $row = 1;
    
    while ( my @row = $sthx->fetchrow_array() ) {
      my ($R_TS3_NCPDP, $R_TPP, $R_TRN02_Check_Number, $R_BPR02_Check_Amount, $R_BPR16_Date, $R_BPR04_Payment_Method_Code ) = @row;
      
      $R_TS3_NCPDP = sprintf("%07d", $R_TS3_NCPDP);
      
      my $R_BPR16_DateDisplay = substr($R_BPR16_Date, 4, 2) . "/" . substr($R_BPR16_Date, 6, 2) . "/" . substr($R_BPR16_Date, 0, 4);
      
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
      <td class="$row_color" align=right width='100px'style="padding-right:20px">$R_BPR02_Check_Amount</td>
      <td class="$row_color">$R_BPR16_DateDisplay</td>
      <td class="$row_color">$R_BPR04_Payment_Method_Code</td>
      </tr>\n#;
      
      $row++;
    }
    print "</table>\n";
    
    print qq#
    <INPUT TYPE="hidden" NAME="filter_ncpdp" VALUE="$filter_ncpdp" >
    <INPUT TYPE="hidden" ID="filter_in" NAME="filter_in" value = "$filter_in">
    #;
    
    print qq#<hr />#;
    
    print qq#
    <br><br>
    <span><input type="checkbox" name="action" class="action_options" value="excel"> Export to Excel </span><br /><br />
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
  
  my $table = "835remitstb";
  
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

  my $sql = "
    SELECT R_TPP, R_TS3_NCPDP, R_TRN02_Check_Number, R_BPR16_Date, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, R_CheckReceived_Date  
    FROM $DBNAME.$TABLE 
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
    $filename = "Pending_Remits_Report_${filter_in}_${long_time}.xlsx";
    @pcs = split(/-/, $filter_in);
    $id = $pcs[0];
    $id =~ s/\s+//g;
    $TPP_Name = $ThirdPartyPayer_Names{$id};

    $save_location = "D:\\Recon-Rx\\Reports\\";
    $filename =~ s/##/_/g;
    $filename =~ s/ //g;
    my $Pharmacy_Name = $Pharmacy_Names{$PH_ID};
    $Pharmacy_NCPDP = $Pharmacy_NCPDPs{$PH_ID};
    print "save_location: $save_location<br>filename: $filename<br>\n" if ($debug);
    
    print qq#<p class="notification"><img src="/images/xlsx1.png" style="vertical-align: middle"><a href="/Reports/$filename">Download File</a>#;
    print qq#<p><button id="email_template" class="button-form" onclick="etemplate('$Pharmacy_Name ($Pharmacy_NCPDP)','$TPP_Name')">Email Template</button></p>#;
    
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
      
      while ( my @row = $sthee->fetchrow_array() ) {
      my ($R_TPP, $R_TS3_NCPDP, $R_TRN02_Check_Number, $R_BPR16_Date, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount, $R_CheckReceived_Date) = @row;
      
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
    }
  
    $workbook->close(); #End XLSX
    
  }
  $sthee->finish;
  
}


