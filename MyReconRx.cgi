require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$PH_ID = $in{'PH_ID'};

$WHICHDB    = $in{'WHICHDB'};
$PH_ID      = $in{'PH_ID'};
$USER       = $in{'USER'};

##$WHICHDB = 'Webinar' if($USER == 1489);
$Agg_String = $in{'Agg_String'};

($WHICHDB)  = &StripJunk($WHICHDB);

&readsetCookies;

&readPharmacies;

print "Set-Cookie:AreteUser=$Pharmacy_Arete{$PH_ID}; path=/; domain=$cookie_server;\n"  if($Pharmacy_Arete{$PH_ID});
print "Set-Cookie:Agg_String=$Agg_String; path=/; domain=$cookie_server;\n"  if ( $PH_ID  eq 'Aggregated');

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);
#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock_New;
  }
  else {
    if ($USER != 66) {
      &ReconRxHeaderBlock;
	  #&ReconRxHeaderBlockNew;
    }
    else {
      &ReconRxHeaderBlock;
      #&ReconRxHeaderBlockNew;
    }
  }
} else {
   &ReconRxGotoNewLogin;
   exit(0);
}

#______________________________________________________________________________


### Log pharmacy login

if ( $TYPE =~ /^\s*$/ ) {
   if ( $USER !~ m/[^0-9.]/ && $USER > 0 && $OWNER !~ /pharmassess/i) {
      $Pharmacy_Name = $Pharmacy_Names{$USER};
      &logActivity($Pharmacy_Name, "Logged in to ReconRx", $USER);
   } else {
      if ( $USER eq $OWNER ) {
         &logActivity($RUSER, "SuperUser Logged in to ReconRx", NULL);
      }
   }
}

#______________________________________________________________________________
#print "USER : $USER \n";
$dbin     = "R8DBNAME";
if ($USER == 2612) {
    $DBNAME   = "webinar";
	$WHICHDB  = "webinar";
} else {   
    $DBNAME   = $DBNAMES{"$dbin"};
}
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&displayPharmacyRight($PH_ID) if ($PH_ID);

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayPharmacyRight {
  my ($PH_ID) = @_;
  print qq#<!-- displayPharmacyRight -->\n#;

  $ntitle = "Dashboard";
  print qq#<h1 class="page_title">$ntitle</h1>\n#;

  ### Display Dashboard Graphs
 #print "WHICHDB: $WHICHDB\n";
  if ( $WHICHDB =~ /^Webinar$/i ) {
    &Print_Once_Daily_At_a_Glance;
    #&Print_Once_Daily_At_a_Glance_Webinar;
  } else {
    &Print_Once_Daily_At_a_Glance;
  }

  print "sub displayPharmacyRight: Exit.<br>\n" if ($debug);
}
   
#______________________________________________________________________________

sub Print_Once_Daily_At_a_Glance {
 $aggregated = '';
 print "sub Print_Once_Daily_At_a_Glance. Entry. WHICHDB: $WHICHDB<br>\n" if ($debug);

  $Pharmacy_ID  = $PH_ID;
  $fphid        = $PH_ID;
  if($PH_ID =~ /Aggregated/) {
    $fphid  = "$USER";
    $aggregated = '_Aggregated';
  }
  #print "fphid: $fphid\n";

  my $infile = $fphid . ".html";
  my $FILE = "D:\\WWW\\members.recon-rx.com\\Home_Pages$aggregated\\$infile";
  my ($ENV) = &What_Env_am_I_in;

  $FILE = "D:\\WWW\\www.recon-rx.com\\Home_Pages$aggregated\\$infile" if ( $ENV =~ /DEV/i );
  
  #$print "FILE: $FILE\n";
  
  if ( -e $FILE ) {

    $Total   = 0;
    $F1to44  = 0;
    $F45to59 = 0;
    $F60to89 = 0;
    $Fover90 = 0;

    if($PH_ID =~ /Aggregated/) {
       $PH_ID = $Agg_String;
    }
    #print "Agg_String: $Agg_String\n";
    $reconrx_aging_sql = &get_reconrx_aging_sql($PH_ID);

    my $sql =" SELECT sum(dbTotalAmountPaid_Remaining) as 'Total', sum(`1-44 Days`) as a, sum(`45-59 Days`) as b, sum(`60-89 Days`) as c ,sum(`90+ Days`) as d 
               FROM ($reconrx_aging_sql
                    )a
             ";
    #print "sql: $sql\n";
      $sthg = $dbx->prepare($sql);
      $sthg->execute();
    my $numofrows = $sthg->rows;

    while (my @row = $sthg->fetchrow_array()) {
  	($All_Aging, $F1to44, $F45to59, $F60to89, $Fover90) = @row;
    }
    $sthg->finish();

    if ( $WHICHDB =~ /^Webinar$/i ) {
      $All_Aging -=$F60to89;
      $All_Aging -=$Fover90;
      $F60to89 = 0;
      $Fover90 = 0;
    }

    $All_Aging   = &commify(sprintf("%0.2f", $All_Aging));
    $F1to44      = &commify(sprintf("%0.2f", $F1to44));
    $F45to59     = &commify(sprintf("%0.2f", $F45to59));
    $F60to89     = &commify(sprintf("%0.2f", $F60to89));
    $Fover90     = &commify(sprintf("%0.2f", $Fover90));

    open(FILE, "< $FILE") || warn "Couldn't open home page.<br>\n$!<br>\n<br>\n";

    $/ = undef;
    my $body = <FILE>;
    close(FILE);

    $body =~ s/\<All_Aging\>/$All_Aging/;
    $body =~ s/\<F1to44\>/$F1to44/;
    $body =~ s/\<F45to59\>/$F45to59/;
    $body =~ s/\<F60to89\>/$F60to89/;
    $body =~ s/\<Fover90\>/$Fover90/;

    print "<center>\n";
    print $body;  
    print "</center>";
  } else {
    print qq#
	
    <h1 class="page_title">Welcome to ReconRx!</h1>
    <p class="notification">Thank you for joining ReconRx! Your Dashboard has not yet been generated, but will be soon! If you see this message for more than 24 hours, please <a href="Contact_Us.cgi">let us know</a>.</p>
    #;
  }

  print "sub Print_Once_Daily_At_a_Glance. Exit<br>\n" if ($debug);

}

#______________________________________________________________________________

sub Print_Once_Daily_At_a_Glance_Webinar {

 print "sub Print_Once_Daily_At_a_Glance. Entry. WHICHDB: $WHICHDB<br>\n" if ($debug);

  $Pharmacy_ID  = $PH_ID;

  $Total   = 0;
  $F1to44  = 0;
  $F45to59 = 0;
  $F60to89 = 0;
  $Fover90 = 0;

  $sql = "SELECT Total, IFNULL(1to44,0) 1to44, IFNULL(45to59,0) 45to59, IFNULL(60to89,0) 60to89, IFNULL(over90,0) over90
            FROM ( SELECT dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) Total 
                     FROM Webinar.incomingtb
                    WHERE dbTotalAmountPaid_Remaining > 0 
                       && Pharmacy_ID = $Pharmacy_ID
                       && dbBinParent != -1
                       && dbBinParentdbkey NOT IN (SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                     FROM officedb.third_party_payers 
                                                    WHERE Reconcile = 'NO')
                 GROUP BY dbNCPDPNumber
                 ) totals
       LEFT JOIN ( SELECT dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) 1to44
                     FROM Webinar.incomingtb
                    WHERE dbTotalAmountPaid_Remaining > 0
                       && Pharmacy_ID = $Pharmacy_ID
                       && dbBinParent != -1
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 44 DAY) && DATE(dbDateTransmitted) <= CURDATE())
                       && dbBinParentdbkey NOT IN (SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                     FROM officedb.third_party_payers
                                                    WHERE Reconcile = 'NO')
                 GROUP BY dbNCPDPNumber
                 ) set_1to44
              ON set_1to44.dbNCPDPNumber = totals.dbNCPDPNumber
       LEFT JOIN ( SELECT dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) 45to59
                     FROM Webinar.incomingtb
                    WHERE dbTotalAmountPaid_Remaining > 0
                       && Pharmacy_ID = $Pharmacy_ID
                       && dbBinParent != -1
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 59 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY))
                       && dbBinParentdbkey NOT IN (SELECT officedb.third_party_payers.Third_Party_Payer_ID
                                                     FROM officedb.third_party_payers 
                                                    WHERE Reconcile = 'NO')
                 GROUP BY dbNCPDPNumber
                 ) set_45to59
              ON set_45to59.dbNCPDPNumber = totals.dbNCPDPNumber
       LEFT JOIN ( SELECT dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) 60to89 
                     FROM Webinar.incomingtb
                    WHERE dbTotalAmountPaid_Remaining > 0
                       && Pharmacy_ID = $Pharmacy_ID
                       && dbBinParent != -1
                       && (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 89 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 60 DAY))
                       && dbBinParentdbkey NOT IN (SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                     FROM officedb.third_party_payers 
                                                    WHERE Reconcile = 'NO')
                 GROUP BY dbNCPDPNumber
                 ) set_60to89
              ON set_60to89.dbNCPDPNumber = totals.dbNCPDPNumber
       LEFT JOIN ( SELECT dbNCPDPNumber, sum(dbTotalAmountPaid_Remaining) over90 
                     FROM Webinar.incomingtb
                    WHERE dbTotalAmountPaid_Remaining > 0
                       && Pharmacy_ID = $Pharmacy_ID
                       && dbBinParent != -1
                       && (DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
                       && dbBinParentdbkey NOT IN (SELECT officedb.third_party_payers.Third_Party_Payer_ID 
                                                     FROM officedb.third_party_payers
                                                    WHERE Reconcile = 'NO')
                 GROUP BY dbNCPDPNumber
                 ) set_over90
              ON set_over90.dbNCPDPNumber = totals.dbNCPDPNumber";

  if ( $debug ) {
     $sqlout = $sql;
     print "sqlout: $sqlout\n\n";
  }

  $sthg = $dbx->prepare($sql);
  $sthg->execute();
  my $numofrows = $sthg->rows;

  while (my @row = $sthg->fetchrow_array()) {
	($All_Aging, $F1to44, $F45to59, $F60to89, $Fover90) = @row;
  }
  $sthg->finish();
  if ($PH_ID =~ /^11$|^33$|^23$|^4$/ ) {
    $All_Aging -= ($F60to89 + $Fover90);
    $F60to89 = 0;
    $Fover90 = 0;
  }

  $All_Aging = &commify(sprintf("%0.2f", $All_Aging));
  $F1to44    = &commify(sprintf("%0.2f", $F1to44));
  $F45to59   = &commify(sprintf("%0.2f", $F45to59));
  $F60to89   = &commify(sprintf("%0.2f", $F60to89));
  $Fover90   = &commify(sprintf("%0.2f", $Fover90));

  
   $infile = "33.html"  if ($PH_ID == 33);
   $infile = "11.html"  if ($PH_ID == 11);
   $infile = "23.html"  if ($PH_ID == 23);
   $infile = "4.html"   if ($PH_ID == 4);

  my $FILE = "D:\\WWW\\members.recon-rx.com\\Home_Pages\\$infile";
  open(FILE, "< $FILE") || warn "Couldn't open home page. $FILE\\$infile<br>\n$!<br>\n<br>\n";
  $/ = undef;
  my $body = <FILE>;
  close(FILE);

  $body =~ s/\<All_Aging\>/$All_Aging/;
  $body =~ s/\<F1to44\>/$F1to44/;
  $body =~ s/\<F45to59\>/$F45to59/;
  $body =~ s/\<F60to89\>/$F60to89/;
  $body =~ s/\<Fover90\>/$Fover90/;

  print "<center>\n";
  print $body;  
  print "</center>";

  print "sub Print_Once_Daily_At_a_Glance. Exit<br>\n" if ($debug);

}

#______________________________________________________________________________

