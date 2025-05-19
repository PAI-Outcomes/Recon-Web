require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$LDATEADDED = $in{'LDATEADDED'};
$SORT       = $in{'s'};

($SORT) = &StripJunk($SORT);

&readsetCookies;
&readPharmacies;

if ( $USER ) {
  &readCSRs();
  $ram = $CSR_Reverse_ID_Lookup{$USER};

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
$todaysdate = sprintf("%04d-%02d-%02d", $year, $month, $day);

#______________________________________________________________________________
#______________________________________________________________________________

&readThirdPartyPayers;

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

my $TOTAL  = 0;
my $RECPAY = 0;
my $FMT = "%0.02f";
my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );

$dbz = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&update_remitsdb;

$ntitle = "Post Payment to Remit-Missing Payment Research";
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
        { 'bSortable': false, 'aTargets': [ 5,6 ] }
      ]
    }); 
	
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
  
  print qq#<FORM name="prform" id="prform" ACTION="$URLH" METHOD="POST">\n#;

#-----------------------------------------------------------------------------------------------------

  print "<table>\n";

  print qq#<tr><th><label for="NCPDPNumber">Pharmacy:</label></th>#;
  print qq#<th><input type="text" name="NCPDPNumber" list="plist" id="NCPDP" value="$inNCPDP" style="width:300px;">\n#;
  print qq#<datalist id="plist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "pharmacy";

  my $sql = "SELECT Pharmacy_ID, NCPDP, Pharmacy_Name
               FROM officedb.pharmacy 
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
          UNION ALL
             SELECT Pharmacy_ID, NCPDP, CONCAT(Pharmacy_Name, ' (COO)') AS Pharmacy_Name
               FROM officedb.pharmacy_coo
              WHERE (Status_ReconRx = 'Active' OR Status_ReconRx_Clinic = 'Active')
                 && NCPDP NOT IN (1111111,2222222,3333333,4444444,5555555)
           ORDER BY Pharmacy_Name";

  my $sthx  = $dbz->prepare("$sql");
  $sthx->execute;

  while ( my ($PH_ID, $NCPDP, $Pharmacy_Name) = $sthx->fetchrow_array() ) {
    print qq#<option value="$NCPDP - $Pharmacy_Name"> </option>\n#;
  }

  $sthx->finish;
  print qq#</datalist>&nbsp;<INPUT class="button-form" TYPE="submit" NAME="Select" VALUE="Search"></th></tr></table>#;

#-----------------------------------------------------------------------------------------------------

  print "<hr />\n";
  
  print qq#<br /><div style="float: right;"><button style="padding:5px; margin:0px" id="submit_form" NAME="Submit">Move</button></div>\n#;

  print qq#<table id="tablef" class="main">\n#;
  
  print qq#<thead>\n#;
  print qq#<tr>#;
  print qq#<th>NCPDP</th>#;
  print qq#<th>Third Party</th>#;
  print qq#<th>Pmt Type</th>#;
  print qq#<th class="align_center">Check /<br>ACH \#</th>#;
  print qq#<th class="align_center">Amount</th>#;
  print qq#<th class="align_center">Date</th>#;
  print qq#<th class="align_center">Payment Status</th>#;
  print qq#<th class="align_center">Research</th>#;
  print qq#<th class="align_center">Sent</th>#;
  print qq#<th>&nbsp;</th>#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;
  
  &display_lines;
  
  print qq#</tbody>\n#;
  
  my $TOTAL = "\$" . &commify(sprintf("$FMT", $TOTAL));

  print qq#</table>\n#;
  print qq#<br /><div style="float: right;"><button style="padding:5px; margin:5px" id="submit_form" NAME="Submit">Move</button></div>\n#;
  print qq#</FORM>\n#;
  
  print qq#<div style="clear: both;"></div>\n#;
}

#______________________________________________________________________________

sub display_lines {
  my $dbin     = "P8DBNAME";
  my $P8DBNAME   = $DBNAMES{"$dbin"};
  my $P8TABLE    = $DBTABN{"$dbin"};
  $where = '';

  $where = " && a.Pharmacy_ID = $PH_ID " if ( $PH_ID );

  my $sql = "
    SELECT a.R_TPP_PRI, a.R_TPP, b.NCPDP, a.R_BPR04_Payment_Method_Code, a.R_BPR02_Check_Amount, a.R_BPR16_Date,
           a.R_TRN02_Check_Number, a.R_PENDRECV, a.R_PostedBy, c.id, Date_Format(c.research_date,'%m/%d/%Y')
      FROM $DBNAME.checks a
      JOIN officedb.pharmacy b ON (a.pharmacy_id = b.pharmacy_id AND b.ReconRx_Account_Manager = '$ram')
#      JOIN officedb.pharmacy b ON (a.pharmacy_id = b.pharmacy_id)
 LEFT JOIN $DBNAME.remit_research c ON (a.pharmacy_id = c.pharmacy_id 
                                    AND a.R_TPP = c.payer 
                                    AND a.R_BPR04_Payment_Method_Code = c.payment_method 
                                    AND a.R_BPR02_Check_Amount = c.check_amount
                                    AND a.R_BPR16_Date = c.check_date
                                    AND a.R_TRN02_Check_Number = c.check_number)
      WHERE a.R_PENDRECV = 'M'
        $where
        && a.R_TPP_PRI != '700006'
        && a.R_BPR02_Check_Amount != 0.00
        && a.R_CheckReceived_Date IS NULL
         
      GROUP BY a.R_TRN02_Check_Number
      ORDER BY a.R_PENDRECV DESC, a.R_TPP
  ";

  my $sqlout = $sql;
  $sqlout =~ s/\n/<br>\n/g;
  $sqlout =~ s/ /&nbsp/g;
#  print "<hr>sql:<br>$sqlout<hr>\n" ;#if ($debug);
 
  my $stb = $dbz->prepare($sql);
  my $numofrows = $stb->execute;

  if ( $numofrows <= 0 ) {
     print "No records found for this pharmacy<br>\n";
  } else {
    while (my @row = $stb->fetchrow_array()) {
       ($R_TPP_PRI, $R_TPP, $R_TS3_NCPDP, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount, $R_BPR16_Date, $R_TRN02_Check_Number, $R_PENDRECV, $R_PostedBy, $rid, $research_date) = @row;

       $key = "$R_TPP_PRI##$R_TPP##$R_TS3_NCPDP##$R_BPR04_Payment_Method_Code##$R_TRN02_Check_Number##$R_BPR02_Check_Amount##$R_BPR16_Date##$R_PENDRECV##$R_PostedBy##$rid##$research_date";

       $R_TRN02_Check_Number =~ s/\-/ \-<br>/g;

       $TOTAL += $R_BPR02_Check_Amount;
       my $OcheckAmount = sprintf("$FMT", $R_BPR02_Check_Amount);
	   
       my $jdate = $R_BPR16_Date;
       my $year = substr($jdate, 0, 4);
       my $mon  = substr($jdate, 4, 2);
       my $mday = substr($jdate, 6, 2);
       my $sec  = 0; $min = 0; $hour = 0;
       my $mon1 = $mon;
       my $mon  = $mon - 1;
       if ( $R_BPR16_Date > 19000000 ) {
         $Odate = qq#$mon1/$mday/$year#; 
       } else {
         $Odate = 0;
       }

       my $pendrecvname = "PENDRECV##" . "$key";

       $status = 'Missing';
#       $checked = qq#checked="checked"#;
       $addcolor = "red_font";
       if ( $rid || $R_BPR04_Payment_Method_Code =~ /ACH/i ) {
         $select = '<div style="min-width: 16px;"></div>';
       }
       else {
         $select = qq#  <input type="checkbox" name="$pendrecvname" value="M" $checked>#;
       }

       if ( $rid && (!$research_date)) {
         $research_date = 'Pending';
       }
	   
       if ($R_PostedBy =~ /recon/i) {
         $R_PostedByTD = '<img src="/images/reconrx16px.png">';
       } else {
         $R_PostedByTD = '<div style="min-width: 16px;"></div>';
       }

       print qq#<tr class="$addcolor">#;
       print qq#<td class="">$R_TS3_NCPDP</td>#;
       print qq#<td class="">$R_TPP</td>#;
       print qq#<td class="">$R_BPR04_Payment_Method_Code</td>#;
       print qq#<td class="align_center">$R_TRN02_Check_Number</td>#;
       print qq#<td class="align_right">$OcheckAmount</td>#;
       print qq#<td class="">$Odate</td>#;
       print qq#<td class="align_center" nowrap>$status</td>#;
       print qq#<td class="align_center">$select</td>#;
       print qq#<td class="align_center">$research_date</td>#;
       print qq#<td class="">$R_PostedByTD</td>#;
       print qq#</tr>\n#;
    }
  }
  $stb->finish();
}

#______________________________________________________________________________

sub update_remitsdb {
  my ($key, $sql);
  
  foreach $key (sort keys %in) {
     next if ( $key !~ /^PENDRECV/i);

     my ($PR, $R_TPP_PRI, $R_TPP, $R_TS3_NCPDP, $R_BPR04_Payment_Method_Code, $R_TRN02_Check_Number, $R_BPR02_Check_Amount, $R_BPR16_Date, $R_PENDRECV) = split("##", $key);

     $PH_ID = $Reverse_Pharmacy_NCPDPs{$R_TS3_NCPDP};

     $sql  = qq#
       REPLACE INTO $DBNAME.remit_research (pharmacy_id, ncpdp, tpp_id, payer, payment_method, check_number, check_amount, check_date)
       VALUES ($PH_ID, '$R_TS3_NCPDP', $R_TPP_PRI, '$R_TPP', '$R_BPR04_Payment_Method_Code', '$R_TRN02_Check_Number', '$R_BPR02_Check_Amount', '$R_BPR16_Date')
     #;

#     print "$sql<br>";

     $sth99 = $dbz->prepare($sql) || die "Error preparing query" . $dbz->errstr;
     $sth99->execute() or die $DBI::errstr;
     my $NumOfRows = $sth99->rows;
 
     $sth99->finish();
  }
}

#______________________________________________________________________________
