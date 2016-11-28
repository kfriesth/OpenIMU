#include "RecordsDialog.h"
#include <QFileDialog>
#include <QString>
#include<QFile>
#include<QMessageBox>
#include<QtDebug>
#include <fstream>
#include <string>
#include <iostream>

#include "../MainWindow.h"
#include"acquisition/WimuAcquisition.h"
#include "acquisition/CJsonSerializer.h"



RecordsDialog::RecordsDialog(QWidget *parent):QDialog(parent)
{

    m_parent = parent;
    current_uuid = "";

    this->setMinimumSize(300,400);
    this->setMaximumSize(300,400);
    this->setWindowTitle(QWidget::tr("Enregistrements"));

    mainLayout = new QGridLayout(this);
    selectRecord = new QPushButton(QWidget::tr("Sélectionner un enregistrement"));
    folderSelected = new QLabel(QWidget::tr("Dossier séléctionné:"));

    selectedImuLabel = new QLabel(QWidget::tr("Centrale inertielle:"));
    imuSelectComboBox = new QComboBox;
    imuSelectComboBox->addItem(QWidget::tr("WimU"));
    imuSelectComboBox->addItem(QWidget::tr("Deslys trigno"));
    imuSelectComboBox->addItem(QWidget::tr("XSens"));
    selectedImu = new QLabel(QWidget::tr("None"));

    imuPosition = new QLabel(tr("Position: "));
    imuPositionComboBox = new QComboBox;
    imuPositionComboBox->addItem(QWidget::tr("Poignet"));
    imuPositionComboBox->addItem(QWidget::tr("Hanche"));
    imuPositionComboBox->addItem(QWidget::tr("Cheville"));
    imuPositionComboBox->addItem(QWidget::tr("Genoux"));
    imuPositionComboBox->addItem(QWidget::tr("Coude"));
    imuPositionComboBox->addItem(QWidget::tr("Tête"));
    imuPositionComboBox->addItem(QWidget::tr("Cou"));

    recordNaming = new QLabel(tr("Nom de l'enregistrement*:"));
    recordName = new QLineEdit;
    recordName->setMinimumHeight(20);
    recordName->setPlaceholderText(QWidget::tr("Wimu_2016_10_18_PatientX"));

    recordDetails = new QLabel(tr("Détails de l'enregistrement: "));
    userDetails = new QTextEdit();
    userDetails->setMinimumHeight(20);
    userDetails->setMaximumHeight(100);
    addRecord = new QPushButton(QWidget::tr("Ajouter l'enregistrement"));

    spinner = new QLabel();
    movie = new QMovie("../applicationOpenimu/app/icons/upload_loader.gif");
    spinner->setMovie(movie);

    successLabel = new QLabel();

    mainLayout->addWidget(selectRecord,0,0);

    mainLayout->addWidget(folderSelected,1,0);

    mainLayout->addWidget(selectedImuLabel,2,0);
    mainLayout->addWidget(imuSelectComboBox,3,0);
    mainLayout->addWidget(imuPosition,4,0);
    mainLayout->addWidget(imuPositionComboBox,5,0);

    mainLayout->addWidget(recordNaming,6,0);
    mainLayout->addWidget(recordName,7,0);

    mainLayout->addWidget(recordDetails,8,0);
    mainLayout->addWidget(userDetails,9,0);

    mainLayout->addWidget(addRecord,10,0);

    mainLayout->addWidget(spinner,11,0,Qt::AlignCenter);

    mainLayout->addWidget(successLabel,11,0,Qt::AlignCenter);

    connect(addRecord, SIGNAL(clicked()), this, SLOT(addRecordSlot()));

    connect(selectRecord, SIGNAL(clicked()), this, SLOT(selectRecordSlot()));
    connect(imuSelectComboBox, SIGNAL(currentIndexChanged(QString)), selectedImu, SLOT(setText(QString)));

    this->setStyleSheet( "QPushButton{"
                         "background-color: rgba(119, 160, 175,0.7);"
                         "border-style: inset;"
                         "border-width: 0.2px;"
                         "border-radius: 10px;"
                         "border-color: white;"
                         "font: 12px;"
                         "min-width: 10em;"
                         "padding: 6px; }"
                         "QPushButton:pressed { background-color: rgba(70, 95, 104, 0.7);}"
                         );
}

RecordsDialog::~RecordsDialog()
{

}


void RecordsDialog::selectRecordSlot()
{
    QFile *file;
    folderToAdd = QFileDialog::getExistingDirectory(this, tr("Sélectionner dossier"),"/path/to/file/");
    file = new QFile(folderToAdd);
    if(!folderToAdd.isEmpty()){
         folderSelected->setText(tr("Dossier séléctionné: ")+ file->fileName().section("/",-1,-1));
         isFolderSelected = true;
     }else{
          folderSelected->setText(tr(" Aucun dossier séléctionné ") + file->fileName());
          isFolderSelected = false;
     }
}

//*************************** ADD RECORD SLOT *************************
bool RecordsDialog::addRecordFileListToBD(QStringList & fileList, std::string folderPath)
{
    std::string output;
    bool validFolder = false;

    for (int i=0; i<fileList.count(); i++)
    {
        std::string filePathAcc = "";
        std::string filePathGyr = "";
        std::string filePathMag = "";
        validFolder = false;

        if(fileList[i].contains("ACC"))
        {
            filePathAcc =  folderPath +"/"+fileList[i].toStdString();
            validFolder = true;

        }
        else if(fileList[i].contains("GYR"))
        {
            filePathGyr =  folderPath +"/"+fileList[i].toStdString();
            validFolder = true;
        }
        else if(fileList[i].contains("MAG"))
        {
            filePathMag =  folderPath +"/"+fileList[i].toStdString();
            validFolder = true;
        }

        if(validFolder && !recordName->text().isEmpty() && isFolderSelected  )
        {
            WimuAcquisition* wimuData = new WimuAcquisition(filePathAcc,filePathGyr,filePathMag,50);
            wimuData->initialize();
            RecordInfo info;
            info.m_recordName = recordName->text().toStdString();
            info.m_imuType = imuSelectComboBox->currentText().toStdString();
            info.m_imuPosition = imuPositionComboBox->currentText().toStdString();
            info.m_recordDetails = userDetails->toPlainText().toStdString();
            info.m_recordId = "None";
            CJsonSerializer::Serialize(wimuData,info, output);
            QString temp = QString::fromStdString(output);

            if(current_uuid.isEmpty())
            {
                addRecordInDB(temp,true);
            }
            else
            {
                addRecordInDB(temp,false);
            }
        }
        else if(recordName->text().isEmpty() && !isFolderSelected)
        {
            return false;
        }
    }
    return true;
}
void RecordsDialog::addRecordSlot()
{
    MainWindow * mainWindow = (MainWindow*)m_parent;
    mainWindow->setStatusBarText(tr("Insertion de l'enregistrement dans la base de données en cours..."));

    successLabel->setText("");

    QDir* dir = new QDir(folderToAdd);
    dir->setFilter(QDir::Files | QDir::NoDotAndDotDot | QDir::NoSymLinks);

    QFileInfoList list = dir->entryInfoList(QDir::Files | QDir::NoDotAndDotDot | QDir::Dirs);
    bool success = true;
    foreach(QFileInfo finfo, list)
    {
        if (finfo.isDir()) {

            QString temp = "Extraction des données de " + finfo.absoluteFilePath();
            mainWindow->setStatusBarText(temp);
            QDir* subDir = new QDir(finfo.absoluteFilePath());
            QStringList fileList = subDir->entryList();
            if(!addRecordFileListToBD(fileList,finfo.absoluteFilePath().toStdString()))
            {
                QMessageBox messageBox;
                messageBox.warning(0,tr("Avertissement"), "Vérifier le nom de l'enregistrement et qu'un dossier a été séléctionné");
                messageBox.setFixedSize(500,200);
                success = false;
                break;
            }
        }
        else
        {
             QStringList fileList = dir->entryList();
             QString temp = "Extraction des données de " + finfo.absoluteFilePath();
             mainWindow->setStatusBarText(temp);
             if(!addRecordFileListToBD(fileList,folderToAdd.toStdString()))
             {
                 QMessageBox messageBox;
                 messageBox.warning(0,tr("Avertissement"), "Vérifier le nom de l'enregistrement et qu'un dossier a été séléctionné");
                 messageBox.setFixedSize(500,200);
                 success = false;
                 break;
             }
             break;
        }
    }

    if(success)
    {
        //info.m_parentId = "None";
        //CJsonSerializer::Serialize(wimuData,info,output);
        successLabel->setText(tr("L'enregistrement ")+recordName->text()+tr(" à été ajouté avec succès"));
        mainWindow->setStatusBarText(tr("L'enregistrement ")+recordName->text()+tr(" à été ajouté avec succès"));

        QMainWindow* currWin = (QMainWindow*)m_parent;
        MainWindow* win = (MainWindow*)currWin;
        win->getRecordsFromDB();
    }
}

//*************************** DATA BASE ACCESS *************************

// Insert single records

bool RecordsDialog::addRecordInDB(QString& json, bool isSingleRecord)
{

    QNetworkAccessManager *manager = new QNetworkAccessManager();
    QByteArray dataByteArray (json.toStdString().c_str(),json.toStdString().length());                                                                                                                  //Your webservice URL
    QNetworkRequest request;
    if(isSingleRecord)
    {
       request.setUrl(QUrl("http://127.0.0.1:5000/insertrecord"));
    }
    else
    {
        request.setUrl(QUrl("http://127.0.0.1:5000/insertrecord/concat/"+ current_uuid));
    }

    QByteArray postDataSize = QByteArray::number(dataByteArray.size());
    request.setRawHeader("User-Agent", "ApplicationNameV01");
    request.setRawHeader("Content-Type", "application/json");
    request.setRawHeader("Content-Length", postDataSize);

    if (manager) {
    bool result;

    QNetworkReply *reply = manager->post(request, dataByteArray);

    QEventLoop loop;
    result = connect(manager, SIGNAL(finished(QNetworkReply*)), &loop,SLOT(quit()));
    loop.exec();
    reponseRecue(reply);

   }
    return true;
}

void RecordsDialog::reponseRecue(QNetworkReply* reply)
{
    if (reply->error() == QNetworkReply::NoError)
   {
       std::string strJson = reply->readAll();
       Json::Value root;
          Json::Reader reader;
          bool parsingSuccessful = reader.parse( strJson.c_str(), root );     //parse process
          if ( !parsingSuccessful )
          {
              std::cout  << "Failed to parse"
                     << reader.getFormattedErrorMessages();
          }
          current_uuid = QString::fromStdString(root.get("valeuruuid", "A Default Value if not exists" ).asString());
   }
   else
   {
       qDebug() << "error connect";
       qWarning() << "ErrorNo: "<< reply->error() << "for url: " << reply->url().toString();
       qDebug() << "Request failed, " << reply->errorString();
       qDebug() << "Headers:"<<  reply->rawHeaderList()<< "content:" << reply->readAll();
       qDebug() << reply->readAll();
   }
   delete reply;
}
